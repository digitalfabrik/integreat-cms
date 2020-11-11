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
