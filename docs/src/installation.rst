************
Installation
************

.. Note::

    If you want to develop on Windows, we suggest using the `Windows Subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/>`_ in combination with `Ubuntu <https://ubuntu.com/wsl>`_ and `postgresql <https://wiki.ubuntuusers.de/PostgreSQL/>`__ as local database server.


Prerequisites
=============

Following packages are required before installing the project (install them with your package manager):

* `git <https://git-scm.com/>`_
* `npm <https://www.npmjs.com/>`_ version 7 or later
* `nodejs <https://nodejs.org/>`_ version 22 or later
* `uv <https://docs.astral.sh/uv/>`_ to manage the Python dependencies
* Either `postgresql <https://www.postgresql.org/>`_ **or** `docker <https://www.docker.com/>`_ to run a local database server
* `gettext <https://www.gnu.org/software/gettext/>`_ and `pcregrep <https://pcre.org/original/doc/html/pcregrep.html>`_ to use the translation features

.. Note::

    A system-wide Python installation is not required. ``uv`` provisions an interpreter which
    satisfies the ``requires-python`` constraint of :github-source:`pyproject.toml` on its own.


Prerequisites on common distributions
-------------------------------------

In the following, we provide the commands to install all these prerequisites on popular distributions.

.. raw:: html

    <details>
    <summary><a>Ubuntu 22.04 LTS (Jammy Jellyfish) / Debian 11 ("Bullseye")</a></summary>
    <br>

::

    # Install basic requirements
    sudo apt install -y apt-transport-https curl gettext git pcregrep libcairo2
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add PPA repository for NodeJS
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    # Add PPA repository for Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    # Install Docker and NodeJS
    sudo apt-get update && apt-cache policy docker-ce && sudo apt install -y containerd.io docker-ce docker-ce-cli nodejs

.. raw:: html

    <details>
    <summary><a>Ubuntu 20.04 LTS (Focal Fossa) / Debian 10 (Buster)</a></summary>
    <br>

::

    # Install basic requirements
    sudo apt install -y apt-transport-https curl gettext git pcregrep libcairo2
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add PPA repository for NodeJS
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    # Add PPA repository for Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    # Install Docker and NodeJS
    sudo apt-get update && apt-cache policy docker-ce && sudo apt install -y containerd.io docker-ce docker-ce-cli nodejs

.. raw:: html

    </details><br>
    <details>
    <summary><a>Arch Linux</a></summary><br>

.. Note::

    This assumes you have completed a basic system installation including a web browser etc. and a helper for the `AUR <https://aur.archlinux.org/>`_, e.g. `yay <https://github.com/Jguer/yay>`_.

::

    # Install requirements
    yay -S docker gettext git netcat nodejs-lts-hydrogen npm pcre uv

.. raw:: html

    </details><br>


Download sources
================

.. highlight:: bash

Clone the project, either

.. container:: two-columns

    .. container:: left-side

        via SSH:

        .. parsed-literal::

            git clone git\@github.com:|github-username|/|github-repository|.git
            cd |github-repository|

    .. container:: right-side

        or HTTPS:

        .. parsed-literal::

            git clone \https://github.com/|github-username|/|github-repository|.git
            cd |github-repository|


Install dependencies and local package
======================================

And install it using our developer tool :github-source:`tools/install.sh`::

    ./tools/install.sh

.. Note::

    - This script checks whether the required system-dependencies are installed and installs the project-dependencies via npm and uv.
      If only one of both dependency-managers should be invoked, run ``npm ci`` or ``uv sync --locked`` directly.

    - By default, ``uv`` selects a suitable Python interpreter itself. To use a specific one which is
      already installed on your system, pass it to the installation script: ``./tools/install.sh --python python3.13``
