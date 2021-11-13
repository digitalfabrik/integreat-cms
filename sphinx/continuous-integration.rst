*********************************
Continuous Integration (CircleCI)
*********************************

.. admonition:: What is continuous integration?

   Continuous integration (CI) is a software development strategy that increases the speed of development while ensuring
   the quality of the code that teams deploy. Developers continually commit code in small increments (at least daily, or
   even several times a day), which is then automatically built and tested before it is merged with the shared repository.

   Source: `CircleCI documentation <https://circleci.com/continuous-integration/>`__


Configuration
=============

Our CircleCI configuration resides in :github-source:`.circleci/config.yml`.
It contains all the jobs listed below.
See `Configuring CircleCI <https://circleci.com/docs/2.0/configuration-reference/>`__ for a full reference.


Workflow ``develop``
====================

This workflow gets triggered everytime a commit is pushed to the ``develop`` branch or a PR is opened.

.. image:: images/circleci-main-workflow.png
    :alt: CircleCI main workflow

.. _circleci-pipenv-install:

pipenv-install
--------------

This job executes ``pipenv install --dev`` and makes use of the `CircleCI Dependency Cache <https://circleci.com/docs/2.0/caching/>`__.
It passes the virtual environment ``.venv`` to the subsequent jobs.

.. _circleci-webpack:

webpack
-------

This job executes ``npm install`` and makes use of the `CircleCI Dependency Cache <https://circleci.com/docs/2.0/caching/>`__.
After that, it compiles all static files with webpack (``npm run prod``) and passes the output in
``integreat_cms/static/dist`` to the subsequent jobs.

pylint
------

This job executes ``pipenv run pylint_runner``, which checks whether the :ref:`pylint` throws any errors or warnings.

black
-----

This job executes ``pipenv run black --check .``, which checks whether the code matches the :ref:`black-code-style` code style.

tests
-----

This job runs the unit tests. It sets up a temporary postgres database and runs the migrations before testing.
It uses the command ``pipenv run integreat-cms-cli test cms --set=COVERAGE`` and
passes the coverage in the ``htmlcov`` directory to the build artifacts.

check-translations
------------------

This job uses the dev-tool ``./dev-tools/check_translations.sh`` to check whether the translation file is up to date and
does not contain any empty or fuzzy entries.

.. _circleci-compile-translations:

compile-translations
--------------------

This job compiles the translation file and passes the resulting ``django.mo`` to the packaging job.

bump-dev-version
----------------

This job modifies the ``bumpver`` config to make sure the changes are only temporary and not committed, then it bumps
the version to the next alpha version which is not yet published on
`TestPyPI <https://test.pypi.org/project/integreat-cms/#history>`__.

.. _circleci-build-package:

build-package
-------------

This job creates a python package and passes the resulting files in ``dist`` to the :ref:`circleci-publish-package` job.
See :doc:`packaging` for more information.

.. _circleci-publish-package:

publish-package
---------------

This job publishes the built package to `TestPyPI <https://test.pypi.org/project/integreat-cms/>`__ via :doc:`twine:index`.

build-documentation
-------------------

This job checks whether the documentation can be generated without any errors by running
``pipenv run ./dev-tools/generate_documentation.sh``.
It passes the html documentation in ``docs`` to the :ref:`circleci-deploy-documentation` job.

.. _circleci-deploy-documentation:

deploy-documentation
--------------------

This job authenticates as the user `DigitalfabrikMember <https://github.com/DigitalfabrikMember>`_ and commits all changes to the
documentation to the branch `gh-pages <https://github.com/Integreat/cms-django/tree/gh-pages>`_
which is then deployed to ``https://integreat.github.io/cms-django/`` by GitHub.

.. _circleci-shellcheck:

shellcheck/check
----------------

This job makes use of the `ShellCheck CircleCI Orb <https://circleci.com/developer/orbs/orb/circleci/shellcheck>`_ and
executes the pre-defined job ``shellcheck/check``. It is configured to check the directory :github-source:`dev-tools`
and to allow external sources because all dev tools source one common function script. Also see :ref:`shellcheck`.


Workflow ``main``
=================

This workflow gets executed when a commit is pushed to the ``main`` branch. Typically, this is a release PR from ``develop``.

pipenv-install
--------------

See :ref:`circleci-pipenv-install`.

bump-version
------------

This job authenticates as the deliverino app and runs ``pipenv run bumpver update`` to bump the version and commit the
changes to the main branch. Additionally, it merges the version bump commit into the ``develop`` branch.


Workflow ``deploy``
===================

This workflow gets executed when a commit is tagged.

pipenv-install
--------------

See :ref:`circleci-pipenv-install`.

webpack
-------

See :ref:`circleci-webpack`.

compile-translations
--------------------

See :ref:`circleci-compile-translations`.

build-package
-------------

See :ref:`circleci-build-package`.

publish-package
---------------

See :ref:`circleci-build-package`. The only difference is that PyPI is used as repository instead of TestPyPI.

create-release
--------------

This job authenticates as Deliverino app and creates a GitHub release with :github-source:`.circleci/scripts/create_release.py`.

notify-mattermost
-----------------

This job sends a release notification to Mattermost into the ``integreat-releases`` channel. It needs the Mattermost
webhook which is injected via the ``mattermost`` context.


Debugging with SSH
==================

If you encounter any build failures which you cannot reproduce on your local machine, you can SSH into the build
server and examine the problem. See `Debugging with SSH <https://circleci.com/docs/2.0/ssh-access-jobs/>`__ for
more information.


.. _circleci-unauthorized:

⚠ Unauthorized (CircleCI)
=========================

.. admonition:: Got error "Unauthorized"?
    :class: error

    Some jobs need secrets that are passed into the execution via `contexts <https://circleci.com/docs/2.0/contexts/>`_.
    If you get the error "unauthorized", you have to make sure you have the correct permissions to access these secrets.
    See :ref:`troubleshooting-unauthorized` for typical solutions to this problem.
