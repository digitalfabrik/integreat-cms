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
* `nodejs <https://nodejs.org/>`_ version 12 or version 14 or higher
* `python3.7 <https://packages.ubuntu.com/search?keywords=python3.7>`_ (`Debian-based distributions <https://en.wikipedia.org/wiki/Category:Debian-based_distributions>`_, e.g. `Ubuntu <https://ubuntu.com>`__ [#ppa]_) / `python37 <https://aur.archlinux.org/packages/python37/>`_ (`Arch-based distributions <https://wiki.archlinux.org/index.php/Arch-based_distributions>`_)
* `python3.7-dev <https://packages.ubuntu.com/search?keywords=python3.7-dev>`_ (only required on `Debian-based distributions <https://en.wikipedia.org/wiki/Category:Debian-based_distributions>`_, e.g. `Ubuntu <https://ubuntu.com>`__)
* `python3-pip <https://packages.ubuntu.com/search?keywords=python3-pip>`_ (`Debian-based distributions <https://en.wikipedia.org/wiki/Category:Debian-based_distributions>`_, e.g. `Ubuntu <https://ubuntu.com>`__) / `python-pip <https://www.archlinux.de/packages/extra/x86_64/python-pip>`_ (`Arch-based distributions <https://wiki.archlinux.org/index.php/Arch-based_distributions>`_)
* `pipenv <https://pipenv.pypa.io/en/latest/>`_ for python3 [#pip]_
* Either `postgresql <https://www.postgresql.org/>`_ **or** `docker <https://www.docker.com/>`_ to run a local database server
* `gettext <https://www.gnu.org/software/gettext/>`_ and `pcregrep <https://pcre.org/original/doc/html/pcregrep.html>`_ to use the translation features

.. Note::

    .. [#ppa] If your distro does not contain python3.7, you first have to add a ppa repository, e.g. ``sudo add-apt-repository ppa:deadsnakes/ppa``.

.. Note::

    .. [#pip] If no recent version of pipenv is packaged for your distro, use ``pip3 install pipenv --user``.

        You might have to add ``export PATH=$PATH:~/.local/bin`` to your default shell config (e.g. ``~/.bashrc`` or ``~/.zshrc``).

        .. include:: include/pipenv-path-environment-variable.rst



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


Create debian package
=====================

Packaging for Debian can be done with setuptools::

    pip3 install stdeb --user
    python3 setup.py --command-packages=stdeb.command bdist_deb

The project requires the package python3-django-widget-tweaks which has to be built manually::

    git clone git@github.com:jazzband/django-widget-tweaks.git
    cd django-widget-tweaks
    pip3 install stdeb
    python3 setup.py --command-packages=stdeb.command bdist_deb

Then install both packages with gdebi::

    apt install gdebi postgresql
    gdebi django-widget-tweaks/deb_dist/python3-django-widget-tweaks_1.4.3-1_all.deb
    gdebi |github-repository|/deb_dist/python3-integreat-cms_0.0.13-1_all.deb

In the end, create a PostgreSQL user and database and adjust the ``/usr/lib/python3/dist-packages/backend/settings.py``.

.. Note::

    In some cases, you can just use the developer tool :github-source:`dev-tools/package.sh`::

        ./dev-tools/package.sh
