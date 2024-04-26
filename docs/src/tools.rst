***************
Developer Tools
***************

This is a collection of scripts which facilitate the development process.
They are targeted at as much platforms and configurations as possible, but there might be edge cases in which they don't work as expected.


Installation
============

Install all project dependencies and the local python package with :github-source:`tools/install.sh`::

    ./tools/install.sh [--clean] [--pre-commit] [--python=PYTHON_COMMAND]

**Options:**

* ``--clean``: Remove all installed dependencies in the ``.venv/`` and ``node_modules/`` directories as well as compiled
  static files in ``integreat_cms/static/dist/``. Existing outdated JavaScript files in these directories can cause compilation
  failures for the :doc:`frontend-bundling`.

* ``--pre-commit``: Install all :ref:`pre-commit-hooks` (can also be manually performed via ``pre-commit install``)

* ``--python``: Use the ``PYTHON_COMMAND`` (e.g. ``python3.9``) to create the virtual environment instead of the default ``python3``

Update all project dependencies and fix security issues with :github-source:`tools/update_dependencies.sh`::

    ./tools/update_dependencies.sh

Create portable debian package with :github-source:`tools/package.sh`::

    ./tools/package.sh


Development Server
==================

Run the inbuilt local webserver with :github-source:`tools/run.sh`::

    ./tools/run.sh [--fast]

**Options:**

* ``--fast``: Skip migrations and translation on startup and just start WebPack and Django


Database
========

Migrate the database with :github-source:`tools/migrate.sh`::

    ./tools/migrate.sh

Import initial test data with :github-source:`tools/loadtestdata.sh`::

    ./tools/loadtestdata.sh

Create a new superuser with :github-source:`tools/create_superuser.sh`::

    ./tools/create_superuser.sh

Delete all database content with :github-source:`tools/prune_database.sh`::

    ./tools/prune_database.sh


.. _translations:

Translations
============

Perform ``makemessages`` and ``compilemessages`` in one step with :github-source:`tools/translate.sh`::

    ./tools/translate.sh

Resolve merge/rebase conflicts with :github-source:`tools/resolve_translation_conflicts.sh`::

    ./tools/resolve_translation_conflicts.sh

Check whether your translations is up-to-date with :github-source:`tools/check_translations.sh`::

    ./tools/check_translations.sh


Testing
=======

Run tests and generate coverage report with :github-source:`tools/test.sh`::

    ./tools/test.sh [--changed] [-v[v[v[v]]]] [TEST_PATH]

**Arguments:**

* ``TEST_PATH``: Run only tests in ``TEST_PATH``

**Options:**

* ``--changed``: Run only tests affected by recent changes

* ``-v``, ``-vv``, ``-vvv``, ``-vvvv``: Verbosity levels, passed directly to pytest.
  Notice that if none are specified, we automatically pass ``--quiet``
  and run tests on multiple CPUs using xdist, resulting in much shorter wait times.

If tests comparing the contents of PDF files fail repeatedly despite you not touching anything related to it, you can try to prune the PDF cache::

    ./tools/prune_pdf_cache.sh


.. _management-command-tool:

Management Commands
===================

Set the environment variables to execute ``django-admin`` management commands
with :github-source:`tools/integreat-cms-cli`::

    ./tools/integreat-cms-cli COMMAND

**Arguments:**

* ``COMMAND``: Invoke the management command ``COMMAND``. List all available commands with ``help``.


Code Quality
============

(Deprecated) Automatically apply our python style with :github-source:`tools/black.sh`::

    ./tools/black.sh

Automatically apply our python style with :github-source:`tools/ruff.sh`::

    ./tools/ruff.sh

Automatically apply our CSS/JS style with :github-source:`tools/prettier.sh`::

    ./tools/prettier.sh

Automatically apply our HTML formatting with :github-source:`tools/djlint.sh`::

    ./tools/djlint.sh

Check the code for semantic correctness with :github-source:`tools/pylint.sh`::

    ./tools/pylint.sh

Execute all tools at once with :github-source:`tools/code_style.sh`::

    ./tools/code_style.sh


Release Notes
=============

Generate the release notes with :github-source:`tools/make_release_notes.sh`::

    ./tools/make_release_notes.sh [--format FORMAT] [--language LANGUAGE] [--output OUTPUT] [--version VERSION] [--all] [--no-heading] [--no-subheading]

**Options:**

* ``--format FORMAT``: The target format of the release notes (must be one of ``md``, ``rst``, ``raw``, defaults to ``md``)
* ``--language LANGUAGE``: The language of the release notes (must be one of ``en``, ``de``, defaults to ``en``)
* ``--output OUTPUT``: Write the release notes to ``OUTPUT`` (defaults to ``/dev/stdout``)
* ``--version VERSION``: Only return the entries of ``VERSION``
* ``--all``: Whether to include all versions (only the latest per default)
* ``--no-heading``: Whether to omit the "Release notes" heading in the document
* ``--no-subheading``: Whether to omit the version subheading in the document (only takes effect when ``--version`` is given)

Create a new release note with :github-source:`tools/new_release_note.sh`::

    ./tools/new_release_note.sh ISSUE LANGUAGE TEXT [--overwrite]

**Arguments:**

* ``ISSUE``: The issue or PR number on GitHub
* ``LANGUAGE``: The language of the following text (must be one of "de", "en")
* ``TEXT``: The release note itself

**Options:**

* ``--overwrite``: Whether to overwrite existing release notes


Documentation
=============

Generate this documentation with :github-source:`tools/make_docs.sh`::

    ./tools/make_docs.sh [--clean] [--make-clean]

**Options:**

* ``--clean``: Remove all temporary documentation files in the ``docs/src/ref/`` and ``docs/src/ref-ext/``
  directories as well as the compiled html output in ``docs/dist``. Existing outdated documentation files can cause the
  generation script to fail if e.g. source files were added or deleted.
* ``--make-clean``: Identical to ``--clean``, but don't proceed after cleaning the environment.


GitHub Review Checker
=====================

Check your current review score with :github-source:`tools/have_i_reviewed_enough.sh`::

    ./tools/have_i_reviewed_enough.sh [--since=DATE]

**Options:**

* ``--since=DATE``: Only take PRs into account which were updated after ``DATE`` (e.g. ``2023-01-01``, ``-2 months`` or ``last week``)


Included Functions
==================

All scripts ``source`` the file :github-source:`tools/_functions.sh` which defines re-usable functions and variables.


Debugging
=========

To get verbose diagnostic output from all bash scripts, you can pass the parameter ``--verbose`` to all scripts.
This will activate both the bash options ``verbose`` and ``xtrace`` (see `set — Linux manual page <https://man7.org/linux/man-pages/man1/set.1p.html>`_)
