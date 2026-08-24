****************
Testing (Pytest)
****************


We use :doc:`pytest <pytest:index>` to validate that the functionality of the cms works as expected.

In addition, we use the following plugins:

* :doc:`pytest-cov <pytest-cov:index>`: This plugin produces coverage reports.
* :doc:`pytest-django <pytest-django:index>`: Provide a few helpers for Django
* :doc:`pytest-xdist:index`: Enable distributing tests across multiple CPUs to speed up test execution
* :doc:`requests-mock:index`: Mocking requests to external APIs

For more information, see :doc:`django:topics/testing/index` and :doc:`django:topics/testing/overview`.

For reference of our test framework and test cases, see :mod:`tests`.


Running Tests
=============

By default ``./tools/test.sh`` runs the suite inside a Docker container that
mirrors the CircleCI environment (same Python, OS and PostgreSQL versions,
see ``docker-compose.test.yml``), so a local run matches CI by construction.
Pass ``--local`` to run directly on the host instead.

Run the full test suite (in Docker)::

    ./tools/test.sh

Run the full test suite on the host::

    ./tools/test.sh --local

Run only **unit tests** (no database, completes in seconds)::

    ./tools/test.sh -m unit

Run everything **except slow** parametrized view tests::

    ./tools/test.sh -m "not slow"

Run a **specific test** by keyword::

    ./tools/test.sh -v -k test_tree_mutex

Run with **fewer roles** for faster local iteration (4 representative roles
instead of 11)::

    QUICK_ROLES=1 ./tools/test.sh

These options can be combined::

    QUICK_ROLES=1 ./tools/test.sh -m "not slow" -v


Test Markers
============

Tests are categorized with pytest markers:

``unit``
    Pure logic tests with no database or external service dependencies.
    These run in about one second.

``slow``
    Tests that take a long time because they run many parametrized variants.
    This includes the 16 ``test_view_status_code_*.py`` files and region
    duplication tests.

Mark your tests appropriately when adding new ones::

    @pytest.mark.unit
    def test_my_pure_function():
        assert compute(42) == expected

    @pytest.mark.slow
    @pytest.mark.django_db
    @pytest.mark.parametrize("role", ALL_ROLES)
    def test_many_variants(role):
        ...


Test Categories
===============

Unit Tests
----------

Unit tests verify pure logic with no side effects. They do **not** touch the
database, filesystem, or network.

- Mark with ``@pytest.mark.unit``
- Do **not** use ``@pytest.mark.django_db``
- Import constants from ``tests.constants``, not ``tests.conftest``
- Examples: ``test_rounded_hix_value.py``, ``test_translation_utils.py``,
  ``test_recurrence_rule.py``

Integration Tests (standard)
----------------------------

Most tests fall into this category. They use the database via pytest-django's
savepoint rollback mechanism (each test runs inside a transaction that is
rolled back after the test).

- Mark with ``@pytest.mark.django_db``
- Request the ``load_test_data`` fixture to access the shared test data
- Database changes are **automatically rolled back** after each test
- Example::

      @pytest.mark.django_db
      def test_something(load_test_data):
          region = Region.objects.get(slug="augsburg")
          assert region.name == "Stadt Augsburg"

Transactional Tests
-------------------

Some tests need real transactions (e.g., testing signals, tree operations,
or management commands that call ``TRUNCATE``). These use
``transaction=True`` which **flushes the database** after each test.

- Mark with ``@pytest.mark.order("last")`` **and**
  ``@pytest.mark.django_db(transaction=True)``
- Request ``load_test_data_transactional`` instead of ``load_test_data``
  (it reloads fixtures per test function)
- The ``order("last")`` marker is required because transactional tests flush
  the database — running them before non-transactional tests in the same
  process would destroy the session-scoped test data
- Example::

      @pytest.mark.order("last")
      @pytest.mark.django_db(transaction=True)
      def test_management_command(load_test_data_transactional):
          call_command("my_command")
          assert ...


Fixtures
========

Shared Fixtures (``tests/conftest.py``)
---------------------------------------

``load_test_data``
    Session-scoped. Ensures the JSON fixtures are loaded. Most tests should
    request this.

``load_test_data_transactional``
    Function-scoped. Reloads JSON fixtures for each transactional test.

``login_role_user``
    Session-scoped, parametrized over all roles. Returns
    ``(Client, role_name)``. Tests using this fixture automatically run once
    per role. Since the client is shared, any state Django keeps in cookies
    outlives the test that created it — unread messages are dropped
    automatically by the autouse ``clear_leaked_messages`` fixture, but tests
    that set other cookies have to clean up after themselves.

Factory Fixtures (``tests/conftest.py``)
----------------------------------------

The ``create_*`` fixtures are function-scoped factory fixtures: each returns a
callable that creates the corresponding model instance with sensible defaults
for all required fields, so tests only need to pass the values they care
about. Prefer them over raw ``objects.create()`` calls::

    @pytest.mark.django_db
    def test_page_creation(create_region, create_page, create_page_translation):
        region = create_region()
        page = create_page(region)
        translation = create_page_translation(page, title="My Page")
        assert translation.title == "My Page"

Available factory fixtures:

- ``create_language(slug=None, **overrides)``
- ``create_region(slug=None, **overrides)`` — also creates a default language
- ``create_page(region, parent=None, **overrides)``
- ``create_page_translation(page, language=None, **overrides)``
- ``create_event(region, start=None, end=None, **overrides)``
- ``create_event_translation(event, language=None, **overrides)``
- ``create_recurrence_rule(**overrides)``
- ``create_user(username=None, **overrides)``


Role Constants (``tests/constants.py``)
---------------------------------------

Import role identifiers from ``tests.constants``::

    from tests.constants import ROOT, ANONYMOUS, STAFF_ROLES, PRIV_STAFF_ROLES

Available constants:

- Individual roles: ``ROOT``, ``ANONYMOUS``, ``MANAGEMENT``, ``EDITOR``,
  ``AUTHOR``, ``EVENT_MANAGER``, ``OBSERVER``, ``CMS_TEAM``,
  ``SERVICE_TEAM``, ``MARKETING_TEAM``
- Role groups: ``WRITE_ROLES``, ``REGION_ROLES``, ``STAFF_ROLES``,
  ``PRIV_STAFF_ROLES``, ``HIGH_PRIV_STAFF_ROLES``, ``ROLES``, ``ALL_ROLES``


Writing New Tests
=================

Adding a View Test
------------------

1. **Status code tests** (does every role get the correct HTTP status?):
   Add entries to ``tests/cms/views/view_config.py``. Each entry is a tuple
   of ``(view_name, allowed_roles)`` grouped by shared URL kwargs. The 16
   ``test_view_status_code_*.py`` files automatically pick up new entries.

2. **Behavior tests** (does the view do the right thing?):
   Create a new test file in the appropriate subdirectory under
   ``tests/cms/views/``. Request ``load_test_data`` and ``login_role_user``::

       @pytest.mark.django_db
       def test_my_view_creates_thing(load_test_data, login_role_user):
           client, role = login_role_user
           response = client.post(reverse("my_view", kwargs={...}), data={...})
           if role in PRIV_STAFF_ROLES:
               assert response.status_code == 302
           else:
               assert response.status_code == 403

Adding an API Test
------------------

API tests live in ``tests/api/`` and typically compare JSON output against
expected output files in ``tests/api/expected-outputs/``.

1. Create the test function using the API client
2. Create the expected output JSON file
3. Assert that the response matches the expected output

When API output changes (e.g., new fields, changed formatting), regenerate all
snapshot files at once::

    ./tools/test.sh -v -k test_api_result --update-snapshots

Then review the diff with ``git diff`` and commit the updated files.

Adding a Management Command Test
---------------------------------

Management command tests live in ``tests/core/management/commands/``.
If the command modifies the database destructively, use a transactional test::

    @pytest.mark.django_db(transaction=True)
    def test_my_command(load_test_data_transactional):
        call_command("my_command", "--flag")
        assert MyModel.objects.count() == expected


Common Pitfalls
===============

1. **Always add** ``@pytest.mark.order("last")`` **to transactional tests** —
   while pytest-django sorts transactional tests after non-transactional ones,
   other collection hooks can reorder tests afterwards and place a
   transactional test (which flushes the database) before non-transactional
   ones. ``@pytest.mark.order("last")`` from pytest-order re-enforces the
   correct ordering after all collection hooks have run.

2. **Don't use** ``serialized_rollback=True`` — it has FK ordering issues
   with PostgreSQL. Use ``load_test_data_transactional`` instead.

3. **Clean up state you attach to session-scoped fixtures** — database changes
   are rolled back after every non-transactional test, but the Python objects
   returned by session-scoped fixtures are not: they live for the whole worker
   process. The most common case is the ``Client`` returned by
   ``login_role_user``, whose cookies survive the test that set them::

       @pytest.mark.django_db
       def test_pagination_cookie(login_role_user):
           client, role = login_role_user
           client.cookies["page_size"] = "50"
           try:
               ...
           finally:
               client.cookies.pop("page_size", None)

   The same applies to anything else cached in the fixture's return value —
   only the rows it points at are reset between tests, not the object itself.

4. **Import role constants from** ``tests.constants``, not ``tests.conftest``.

5. **Tree models** (Page, LanguageTreeNode) must be created with
   ``Page.add_root()`` / ``parent.add_child()``, not ``Page.objects.create()``.


Coverage
========

A full run of ``./tools/test.sh`` collects coverage and enforces the minimum
total coverage configured in ``pyproject.toml`` (``fail_under``). Filtered
runs (``-k``/``-m``/a test path) are not instrumented at all — they only ever
see a subset of the suite, and skipping the coverage tracer keeps them fast.
The per-container runs in CI do collect coverage but do not enforce the
threshold, since each container runs only its share of the tests.

After each run, the test coverage is uploaded to `CodeClimate <https://codeclimate.com/github/digitalfabrik/integreat-cms>`__ (see :ref:`circleci-upload-test-coverage`).


Test API with WebApp
====================

To test the API in the web app with a different CMS server, open the JavaScript console of the web app and execute::

    window.localStorage.setItem('api-url', 'https://cms-test.integreat-app.de')
