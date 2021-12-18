*****************
Production Server
*****************

.. highlight:: bash


.. Note::

    This guide explains how to set up a production server on
    `Ubuntu 20.04.3 LTS (Focal Fossa) <https://releases.ubuntu.com/20.04/>`_. Other linux distributions should work just
    fine, but we don't provide detailed instructions for them.


System requirements
===================

    1. Upgrade all packages::

        sudo apt update && sudo apt -y upgrade

    2. Install system requirements::

        sudo apt -y install python3-venv python3-pip


Integreat CMS Package
=====================

    1. Choose a location for your installation, e.g. ``/opt/integreat-cms/``::

        sudo mkdir /opt/integreat-cms
        sudo chown www-data:www-data /opt/integreat-cms

    2. Create config and log files and set more restrictive permissions::

        sudo touch /var/log/integreat-cms.log /etc/integreat-cms.ini
        sudo chown www-data:www-data /var/log/integreat-cms.log /etc/integreat-cms.ini
        sudo chmod 660 /var/log/integreat-cms.log /etc/integreat-cms.ini

    3. Change to a shell with the permissions of the webserver's user ``www-data``::

        sudo -u www-data bash

    4. Create a virtual environment::

        cd /opt/integreat-cms
        python3 -m venv .venv
        source .venv/bin/activate

    5. Install the Integreat cms inside the virtual environment::

        pip3 install integreat-cms

       .. Note::1

           If you want to set up a test system with the latest changes from the develop branch instead of the main
           branch, use TestPyPI (with the normal PyPI repository a fallback for the dependencies)::

               pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple integreat-cms

    6. Create a symlink to the :github-source:`integreat_cms/core/wsgi.py` file to facilitate the Apache configuration::

        ln -s $(python -c "from integreat_cms.core import wsgi; print(wsgi.__file__)") .

    7. Set the initial configuration by adding the following to ``/etc/integreat-cms.ini`` (for a full list of all
       possible configuration values, have a look at :github-source:`example-configs/integreat-cms.ini`)::

        [integreat-cms]

        SECRET_KEY = <your-secret-key>
        FCM_KEY = <your-firebase-key>
        BASE_URL = https://cms.integreat-app.de
        LOGFILE = /var/integreat-cms.log

    8. Leave the www-data shell::

        exit


Static Files
============

    1. Create root directories for all static files. It's usually good practise to separate code and data, so e.g.
       create the directory ``/var/www/integreat-cms/`` with the sub-directories ``static``, ``media``, ``xliff/upload`` and
       ``xliff/download``::

        sudo mkdir -p /var/www/integreat-cms/{static,media,xliff/{upload,download}}

    2. Make the Apache user ``www-data`` owner of these directories::

        sudo chown -R www-data:www-data /var/www/integreat-cms

    3. Add the static directories to the config in ``/etc/integreat-cms.ini``::

        STATIC_ROOT = /var/www/integreat-cms/static
        MEDIA_ROOT = /var/www/integreat-cms/media
        XLIFF_ROOT = /var/www/integreat-cms/xliff

    4. Collect static files::

        cd /opt/integreat-cms
        sudo -u www-data bash
        source .venv/bin/activate
        integreat-cms-cli collectstatic
        exit


Webserver
=========

    1. Install an `Apache2 <https://httpd.apache.org/>`_ server with `mod_wsgi <https://modwsgi.readthedocs.io/en/develop/>`_::

        sudo apt -y install apache2 libapache2-mod-wsgi-py3

    2. Enable the ``rewrite`` and ``wsgi`` modules::

        sudo a2enmod rewrite wsgi

    3. Setup a vhost for the integreat-cms by using our example config: :github-source:`example-configs/apache2-integreat-vhost.conf`
       and edit the your domain and the paths for static files.


Database
========

    1. Install a `PostgreSQL <https://www.postgresql.org/>`_ database on your system::

        sudo apt -y install postgresql

    2. Create a database user ``integreat`` and set a password::

        sudo -u postgres createuser -P -d integreat

    3. Create a database ``integreat``::

        sudo -u postgres createdb -O integreat integreat

    4. Add the database credentials to the config in ``/etc/integreat-cms.ini``::

        DB_PASSWORD = <your-password>

    5. Execute initial migrations::

        cd /opt/integreat-cms
        sudo -u www-data bash
        source .venv/bin/activate
        integreat-cms-cli migrate


Redis Cache
===========

    1. Install a `Redis <https://redis.io/>`_ database on your system which can be used as cache::

        sudo apt -y install redis-server

    2. Uncomment the following lines in the redis configuration ``/etc/redis/redis.conf`` to make use of unix sockets::

        unixsocket /var/run/redis/redis-server.sock
        unixsocketperm 770

    3. Add the ``www-data`` user to the ``redis`` group to give it access to the socket::

        usermod -aG redis www-data

    4. Configure the integreat-cms to use the redis cache by adding the following values to ``/etc/integreat.ini``::

        REDIS_CACHE = True
        REDIS_UNIX_SOCKET = /var/run/redis/redis-server.sock

Email configuration
===================

    1. Add your SMTP credentials to ``/etc/integreat.ini`` (for the default values, see :github-source:`example-configs/integreat-cms.ini`)::

        EMAIL_HOST = <your-smtp-server>
        EMAIL_HOST_USER = <your-username>
        EMAIL_HOST_PASSWORD = <your-password>
