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
    Fix this by appending it to your default shell config

    .. container:: two-columns

        .. container:: left-side

            for BASH::

                echo "export PATH=\$PATH:~/.local/bin" >> ~/.bashrc

        .. container:: right-side

            for ZSH::

                echo "export PATH=\$PATH:~/.local/bin" >> ~/.zshrc


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
