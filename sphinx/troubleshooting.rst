***************
Troubleshooting
***************

.. highlight:: bash

.. admonition:: General Advice

    If you are experiencing problems of any kind, make sure you have a clean working environment by executing::

        ./dev-tools/install.sh --clean
        ./dev-tools/prune_database.sh

    before trying anything else.

Pipenv not found
================

.. container:: two-columns

    .. container:: left-side

        .. Error:: bash: pipenv: No such file or directory

    .. container:: right-side

        .. Error:: zsh: command not found: pipenv

.. admonition:: Solution
    :class: hint

    Probably you have installed pipenv via pip into ``~/.local/bin``, which is not in your ``PATH`` environment variable.
    Fix this by appending ``export PATH=$PATH:~/.local/bin`` to your default shell config (e.g. ``~/.bashrc`` or ``~/.zshrc``).

    .. include:: include/pipenv-path-environment-variable.rst


Integreat-cms-cli not found
===========================

.. Error:: Error: the command integreat-cms-cli could not be found within PATH or Pipfile's [scripts].

.. admonition:: Solution
    :class: hint

    You have installed an old version of pipenv.
    Probably you used a packaged version of your linux distribution.
    To fix this error, remove the version you have installed with your package manager and use::

        pip3 install pipenv --user

    instead.


Not a git repository
====================

.. Error::

    | Not a git repository
    | To compare two paths outside a working tree:
    | usage: git diff [--no-index] <path> <path>
    | Your translation file is not up to date.
    | Please check if any strings need manual translation.

.. admonition:: Solution
    :class: hint

    If you encounter this problem during a rebase, you probably have installed an old version of git (this bug was fixed
    in `git 2.27.0 <https://github.com/git/git/blob/b3d7a52fac39193503a0b6728771d1bf6a161464/Documentation/RelNotes/2.27.0.txt#L83>`_).

    Check your installed version of git by running::

        git --version

    If your distribution does not package a recent version of git, you might have to add a ppa repository::

        sudo add-apt-repository ppa:git-core/ppa
        sudo apt-get update


.. _troubleshooting-unauthorized:

⚠ Unauthorized (CircleCI)
=========================

.. Error::

    .. image:: images/circleci-unauthorized.png
        :width: 300
        :alt: CircleCI Unauthorized

.. admonition:: Solution
    :class: hint

    If you get this error on your CircleCI build, check the following:

    * Is your GitHub user a member of the `Integreat/cms <https://github.com/orgs/Integreat/teams/cms>`__ team?
    * Is your GitHub account connected with `CircleCI <https://circleci.com/vcs-authorize/>`__?

    See :ref:`circleci-unauthorized` for background information on this error.


MacOS on M1
===========

.. Error::

    | There is no arm64 version of Python 3.7

.. admonition:: Solution
    :class: hint

    Until a compatible version of Python 3.7 was released (the patch has already been merged: `python/cpython#22855 <https://github.com/python/cpython/pull/22855>`_). Until then you can use Python 3.8 instead. Just use homebrew and install it by running::

        brew install python@3.8
    
    Also change `python_version` in `Pipfile` to `3.8`.

.. Error::

    | Error: pg_config executable not found.
    | or
    | ImportError: dlopen(/Users/xyz/Documents/Dev/integreat-cms/.venv/lib/python3.8/site-packages/psycopg2/_psycopg.cpython-38-darwin.so, 2): Symbol not found: _PQbackendPID
    
.. admonition:: Solution
    :class: hint

    There are some issues with the psycopg2 binary package right now. It needs to be compiled locally which requires postgres and libpq::

        brew install libpq postgres --build-from-source 

    The packages need to be built from source as the binary version of postgres is still x86. Building it from source works absolutely fine.
    Afterwards psycopg2 needs to be reinstalled without using your local cache::

        pipenv run pip uninstall psycopg2-binary
        pipenv run pip install psycopg2-binary --no-cache-dir


Webpack Compilation Errors
==========================
.. Error::

    .. code-block:: text

        ERROR in /path/to/integreat-cms/integreat_cms/static/dist/@nodelib/...
        ...
        [tsl] ERROR in ...
        TSXXXX: ...

.. admonition:: Solution
    :class: hint

    There may be remnants of old JavaScript libraries in your installation. Run ``./dev-tools/install --clean`` to remove ``node_modules/`` and ``integreat_cms/static/dist/`` or clean these directories manually.
