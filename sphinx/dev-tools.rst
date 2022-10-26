***************
Developer Tools
***************

This is a collection of scripts which facilitate the development process.
They are targeted at as much platforms and configurations as possible, but there might be edge cases in which they don't work as expected.


Installation
============

Install all project dependencies and the local python package with :github-source:`dev-tools/install.sh`::

    ./dev-tools/install.sh [--clean] [--pre-commit]

**Options:**

* ``--clean``: Remove all installed dependencies in the ``.venv/`` and ``node_modules/`` directories as well as compiled
  static files in ``integreat_cms/static/dist/``. Existing outdated JavaScript files in these directories can cause compilation
  failures for the :doc:`frontend-bundling`.
* ``--pre-commit``: Install all :ref:`pre-commit-hooks` (can also be manually performed via ``pipenv run pre-commit install``)

Update all project dependencies and fix security issues with :github-source:`dev-tools/update_dependencies.sh`::

    ./dev-tools/update_dependencies.sh

Create portable debian package with :github-source:`dev-tools/package.sh`::

    ./dev-tools/package.sh


Development Server
==================

Run the inbuilt local webserver with :github-source:`dev-tools/run.sh`::

    ./dev-tools/run.sh [--fast]

**Options:**

* ``--fast``: Skip migrations and translation on startup and just start WebPack and Django


Database
========

Migrate the database with :github-source:`dev-tools/migrate.sh`::

    ./dev-tools/migrate.sh

Import initial test data with :github-source:`dev-tools/loadtestdata.sh`::

    ./dev-tools/loadtestdata.sh

Create a new superuser with :github-source:`dev-tools/create_superuser.sh`::

    ./dev-tools/create_superuser.sh

Delete all database content with :github-source:`dev-tools/prune_database.sh`::

    ./dev-tools/prune_database.sh


.. _translations:

Translations
============

Perform ``makemessages`` and ``compilemessages`` in one step with :github-source:`dev-tools/translate.sh`::

    ./dev-tools/translate.sh

Resolve merge/rebase conflicts with :github-source:`dev-tools/resolve_translation_conflicts.sh`::

    ./dev-tools/resolve_translation_conflicts.sh

Check whether your translations is up-to-date with :github-source:`dev-tools/check_translations.sh`::

    ./dev-tools/check_translations.sh


Testing
=======

Run tests and generate coverage report with :github-source:`dev-tools/test.sh`::

    ./dev-tools/test.sh


Code Quality
============

Automatically apply our python style with :github-source:`dev-tools/black.sh`::

    ./dev-tools/black.sh

Automatically apply our CSS/JS style with :github-source:`dev-tools/prettier.sh`::

    ./dev-tools/prettier.sh

Check the code for semantic correctness with :github-source:`dev-tools/pylint.sh`::

    ./dev-tools/pylint.sh

Execute all three tools at once with :github-source:`dev-tools/code_style.sh`::

    ./dev-tools/code_style.sh


Documentation
=============

Generate this documentation with :github-source:`dev-tools/generate_documentation.sh`::

    ./dev-tools/generate_documentation.sh [--clean]

**Options:**

* ``--clean``: Remove all temporary documentation files in the ``sphinx/ref/`` and ``sphinx/ref-ext/``
  directories as well as the compiled html output in ``docs``. Existing outdated documentation files can cause the
  generation script to fail if e.g. source files were added or deleted.


Included Functions
==================

All scripts ``source`` the file :github-source:`dev-tools/_functions.sh` which defines re-usable functions and variables.


Debugging
=========

To get verbose diagnostic output from all bash scripts, you can pass the parameter ``--verbose`` to all scripts.
This will activate both the bash options ``verbose`` and ``xtrace`` (see `set — Linux manual page <https://man7.org/linux/man-pages/man1/set.1p.html>`_)
