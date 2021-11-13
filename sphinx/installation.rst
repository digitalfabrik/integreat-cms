************
Installation
************

.. Note::

    If you want to develop on Windows, we suggest using the `Windows Subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/>`_ in combination with `Ubuntu <https://ubuntu.com/wsl>`_ and `postgresql <https://wiki.ubuntuusers.de/PostgreSQL/>`__ as local database server.


Prerequisites
=============

Following packages are required before installing the project (install them with your package manager):

* `git <https://git-scm.com/>`_
* `npm <https://www.npmjs.com/>`_ version 7 or higher
* `nodejs <https://nodejs.org/>`_ version 12 or higher
* `python3.7 <https://packages.ubuntu.com/search?keywords=python3.7>`_ (`Debian-based distributions <https://en.wikipedia.org/wiki/Category:Debian-based_distributions>`_, e.g. `Ubuntu <https://ubuntu.com>`__ [#ppa]_) / `python37 <https://aur.archlinux.org/packages/python37/>`_ (`Arch-based distributions <https://wiki.archlinux.org/index.php/Arch-based_distributions>`_)
* `python3-pip <https://packages.ubuntu.com/search?keywords=python3-pip>`_ (`Debian-based distributions <https://en.wikipedia.org/wiki/Category:Debian-based_distributions>`_, e.g. `Ubuntu <https://ubuntu.com>`__) / `python-pip <https://www.archlinux.de/packages/extra/x86_64/python-pip>`_ (`Arch-based distributions <https://wiki.archlinux.org/index.php/Arch-based_distributions>`_)
* `pipenv <https://pipenv.pypa.io/en/latest/>`_ for python3 [#pip]_
* Either `postgresql <https://www.postgresql.org/>`_ **or** `docker <https://www.docker.com/>`_ to run a local database server
* `gettext <https://www.gnu.org/software/gettext/>`_ and `pcregrep <https://pcre.org/original/doc/html/pcregrep.html>`_ to use the translation features

.. Note::

    .. [#ppa] If your distro does not contain python3.7, you first have to add a ppa repository, e.g. ``sudo add-apt-repository ppa:deadsnakes/ppa``.

    .. [#pip] If no recent version of pipenv is packaged for your distro, use ``pip3 install pipenv --user``.


Prerequisites on common distributions
-------------------------------------

In the following, we provide the commands to install all these prerequisites on popular distributions.

.. raw:: html

    <details>
    <summary><a>Ubuntu 20.04 LTS (Focal Fossa)</a></summary>
    <br>

::

    # Add PPA repository for Python3.7
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    # Install basic requirements
    sudo apt install -y apt-transport-https curl gettext git pcregrep python3.7 python3-pip
    # Add PPA repository for NodeJS
    curl -fsSL https://deb.nodesource.com/setup_15.x | sudo -E bash -
    # Add PPA repository for Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    # Install Docker and NodeJS
    sudo apt-get update && sudo apt install -y containerd.io docker-ce docker-ce-cli nodejs
    # Install Pipenv
    pip3 install pipenv --user


.. raw:: html

    </details><br>
    <details>
    <summary><a>Debian 10 (Buster)</a></summary><br>

.. Note::

    If you're on a completely fresh installation, you need to add your user to the sudoers with::

        su
        /sbin/adduser $USER sudo
        exit

    And then log off and log on again.

::

    # Install basic requirements
    sudo apt install -y apt-transport-https curl gettext git netcat pcregrep python3-pip
    # Add PPA repository for NodeJS
    curl -fsSL https://deb.nodesource.com/setup_15.x | sudo -E bash -
    # Add PPA repository for Docker
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    # Install Docker and NodeJS
    sudo apt-get update && sudo apt install -y containerd.io docker-ce docker-ce-cli nodejs
    # Install Pipenv
    pip3 install pipenv --user


.. raw:: html

    </details><br>
    <details>
    <summary><a>Arch Linux</a></summary><br>

.. Note::

    This assumes you have completed a basic system installation including a web browser etc. and a helper for the `AUR <https://aur.archlinux.org/>`_, e.g. `yay <https://github.com/Jguer/yay>`_.

::

    # Install requirements
    yay -S docker gettext git netcat nodejs-lts-fermium npm pcre python-pip python-pipenv python37

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

And install it using our developer tool :github-source:`dev-tools/install.sh`::

    ./dev-tools/install.sh

.. Note::

    This script checks whether the required system-dependencies are installed and installs the project-dependencies via npm and pipenv.
    If only one of both dependency-managers should be invoked, run ``npm install`` or ``pipenv install --dev`` directly.
