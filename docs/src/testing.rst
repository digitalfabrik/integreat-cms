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

Run the full test suite::

    ./tools/test.sh

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

- Mark with ``@pytest.mark.django_db(transaction=True)``
- Request ``load_test_data_transactional`` instead of ``load_test_data``
  (it reloads fixtures per test function)
- These tests automatically run **after** all non-transactional tests within
  each worker, so they cannot corrupt the session-scoped test data
- Example::

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
    per role.

``login_role_user_async``
    Like ``login_role_user`` but returns an ``AsyncClient``.

``create_page``
    Function-scoped factory fixture for creating pages.

``create_language``
    Function-scoped factory fixture for creating languages.

Factory Functions (``tests/factories.py``)
------------------------------------------

For new tests, prefer the factory functions in ``tests/factories.py`` over
raw ``objects.create()`` calls. Factories provide sensible defaults so you
only specify the fields you care about::

    from tests.factories import make_region, make_page, make_page_translation

    @pytest.mark.django_db
    def test_page_creation():
        region = make_region()
        page = make_page(region)
        translation = make_page_translation(page, title="My Page")
        assert translation.title == "My Page"

Available factories:

- ``make_language(slug=None, **overrides)``
- ``make_region(slug=None, **overrides)`` — also creates a default language
- ``make_page(region, parent=None, **overrides)``
- ``make_page_translation(page, language=None, **overrides)``
- ``make_event(region, start=None, end=None, **overrides)``
- ``make_event_translation(event, language=None, **overrides)``
- ``make_recurrence_rule(**overrides)``
- ``make_user(username=None, **overrides)``


Role Constants (``tests/constants.py``)
---------------------------------------

Import role identifiers from ``tests.constants``::

    from tests.constants import ROOT, ANONYMOUS, STAFF_ROLES, PRIV_STAFF_ROLES

Available constants:

- Individual roles: ``ROOT``, ``ANONYMOUS``, ``MANAGEMENT``, ``EDITOR``,
  ``AUTHOR``, ``EVENT_MANAGER``, ``OBSERVER``, ``CMS_TEAM``,
  ``SERVICE_TEAM``, ``APP_TEAM``, ``MARKETING_TEAM``
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

1. **Don't use** ``@pytest.mark.order`` — pytest-django already ensures
   transactional tests run after non-transactional ones.

2. **Don't use** ``serialized_rollback=True`` — it has FK ordering issues
   with PostgreSQL. Use ``load_test_data_transactional`` instead.

3. **Don't modify session-scoped data** in non-transactional tests — the
   session-scoped fixtures are shared across all tests in a worker. If your
   test needs to modify data, use a transactional test.

4. **Import role constants from** ``tests.constants``, not ``tests.conftest``.

5. **Tree models** (Page, LanguageTreeNode) must be created with
   ``Page.add_root()`` / ``parent.add_child()``, not ``Page.objects.create()``.


Coverage
========

After each run, the test coverage is uploaded to `CodeClimate <https://codeclimate.com/github/digitalfabrik/integreat-cms>`__ (see :ref:`circleci-upload-test-coverage`).


Test API with WebApp
====================

To test the API in the web app with a different CMS server, open the JavaScript console of the web app and execute::

    window.localStorage.setItem('api-url', 'https://cms-test.integreat-app.de')
