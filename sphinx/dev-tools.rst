***************
Developer Tools
***************

This is a collection of scripts which facilitate the development process.
They are targeted at as much platforms and configurations as possible, but there might be edge cases in which they don't work as expected.


Installation
============

Install all project dependencies and the local python package with ``ìnstall.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/install.sh>`__]::

    ./dev-tools/install.sh

Update all project dependencies and fix security issues with ``update_dependencies.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/update_dependencies.sh>`__]::

    ./dev-tools/update_dependencies.sh

Create portable debian package with ``package.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/package.sh>`__]::

    ./dev-tools/package.sh


Development Server
==================

Run the inbuilt local webserver with ``run.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/run.sh>`__]::

    ./dev-tools/run.sh


Database
========

Migrate the database with ``run.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/migrate.sh>`__]::

    ./dev-tools/migrate.sh

Import initial test data with ``loadtestdata.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/loadtestdata.sh>`__]::

    ./dev-tools/loadtestdata.sh

Create a new superuser with ``create_superuser.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/create_superuser.sh>`__]::

    ./dev-tools/create_superuser.sh

Delete all database content with ``prune_database.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/prune_database.sh>`__]::

    ./dev-tools/prune_database.sh


Translations
============

Perform ``makemessages`` and ``compilemessages`` in one step with ``translate.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/translate.sh>`__]::

    ./dev-tools/translate.sh

Resolve merge/rebase conflicts with ``resolve_translation_conflicts.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/resolve_translation_conflicts.sh>`__]::

    ./dev-tools/resolve_translation_conflicts.sh

Check whether your translations is up-to-date with ``check_translations.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/check_translations.sh>`__]::

    ./dev-tools/check_translations.sh


Testing
=======

Run unit tests with ``test.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/test.sh>`__]::

    ./dev-tools/test.sh

Calculate test coverage with ``test_cov.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/test_cov.sh>`__]::

    ./dev-tools/test_cov.sh


Code Quality
============

Check whether the code complies to our style guides with ``pylint.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/pylint.sh>`__]::

    ./dev-tools/pylint.sh


Documentation
=============

Generate this documentation with ``generate_documentation.sh`` [`Source <https://github.com/Integreat/cms-django/blob/develop/dev-tools/generate_documentation.sh>`__]::

    ./dev-tools/generate_documentation.sh
