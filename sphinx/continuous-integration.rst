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
`TestPyPI <https://test.pypi.org/project/integreat-cms/#history>`_.

.. _circleci-build-package:

build-package
-------------

This job creates a debian package with ``python3 setup.py --command-packages=stdeb.command bdist_deb`` and passes the
resulting files in ``dist`` to the build artifacts.

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

.. _circleci-docker-images:

docker-images
-------------
This job builds the docker images used for this CircleCI workflow (see :ref:`circleci-custom-docker-images` for more information).
After a successful docker build, the images are pushed to `Docker Hub <https://hub.docker.com/u/integreat>`__

To login to our organization's docker hub account, the job needs to access the secret ``DOCKER_PASSWORD``, which is
available to all users of the GitHub team `Integreat/cms <https://github.com/orgs/Integreat/teams/cms>`__.
This is also the reason why the job is not executed on branches of the dependabot, because the bot does not have the
permissions to access the Docker Hub credentials.

.. admonition:: Got error "Unauthorized"?
    :class: error

    If you get an ``Unauthorized`` error on this job, see :ref:`circleci-unauthorized`.

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


Debugging with SSH
==================

If you encounter any build failures which you cannot reproduce on your local machine, you can SSH into the build
server and examine the problem. See `Debugging with SSH <https://circleci.com/docs/2.0/ssh-access-jobs/>`__ for
more information.


.. _circleci-custom-docker-images:

Custom Docker Images
====================

To speed up the job :ref:`circleci-build-package`, we use the custom docker image
`integreat/bionic-setuptools <https://hub.docker.com/r/integreat/bionic-setuptools>`__.

.. Note::

    See `Using Custom-Built Docker Images <https://circleci.com/docs/2.0/custom-images/>`__ for more information on custom
    docker images for CircleCI builds.

The Dockerfiles are managed via GitHub in :github-source:`.circleci/images/bionic-setuptools/Dockerfile` and
:github-source:`.circleci/images/python-node-gettext/Dockerfile`.
Every time a change is pushed to GitHub (no matter on which branch), they are tagged with the commit's SHA1 hash and
pushed to `Docker Hub <https://hub.docker.com/u/integreat>`__ (see :ref:`circleci-docker-images` for more information).
Don't forget to change the image tag in :github-source:`.circleci/config.yml` after you made changes to the Dockerfile::

  packaging:
    docker:
      - image: integreat/bionic-setuptools:<INSERT-NEW-COMMIT-SHA1-HERE>
