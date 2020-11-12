***************
Troubleshooting
***************

.. highlight:: bash


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
