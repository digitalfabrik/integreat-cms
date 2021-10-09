*****************
Production Server
*****************

.. highlight:: bash


Integreat CMS Package
=====================

    1. Choose a location for your installation, e.g. ``/opt/integreat-cms/``::

        mkdir /opt/integreat-cms
        cd /opt/integreat-cms

    2. Create a virtual environment::

        python3 -m venv .venv
        source .venv/bin/activate

    3. Install the Integreat cms inside the virtual environment::

        pip3 install integreat-cms


Webserver
=========

    1. Set up an `Apache2 server with mod_wsgi <https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/modwsgi/>`_.
       You can use the :github-source:`example-configs/apache2-integreat-vhost.conf`.

    2. Set the following environment variables in the Apache2 config to ensure a safe and secure service:

        * ``DJANGO_SECRET_KEY``: :attr:`~integreat_cms.core.settings.SECRET_KEY`
        * ``DJANGO_DEBUG``: :attr:`~integreat_cms.core.settings.DEBUG`
        * ``DJANGO_LOGFILE``: :attr:`~integreat_cms.core.settings.LOGFILE`
        * ``DJANGO_WEBAPP_URL``: :attr:`~integreat_cms.core.settings.WEBAPP_URL`
        * ``DJANGO_MATOMO_URL``: :attr:`~integreat_cms.core.settings.MATOMO_URL`
        * ``DJANGO_BASE_URL``: :attr:`~integreat_cms.core.settings.BASE_URL`
        * ``DJANGO_STATIC_ROOT``: :attr:`~integreat_cms.core.settings.STATIC_ROOT`
        * ``DJANGO_MEDIA_ROOT``: :attr:`~integreat_cms.core.settings.MEDIA_ROOT`
        * ``DJANGO_XLIFF_ROOT``: :attr:`~integreat_cms.core.settings.XLIFF_ROOT`

       Database settings: :attr:`~integreat_cms.core.settings.DATABASES`

        * ``DJANGO_DB_HOST``
        * ``DJANGO_DB_NAME``
        * ``DJANGO_DB_PASSWORD``
        * ``DJANGO_DB_USER``
        * ``DJANGO_DB_PORT``

       Email settings:

        * ``DJANGO_EMAIL_HOST``: :attr:`~integreat_cms.core.settings.EMAIL_HOST`
        * ``DJANGO_EMAIL_HOST_PASSWORD``: :attr:`~integreat_cms.core.settings.EMAIL_HOST_PASSWORD`
        * ``DJANGO_EMAIL_HOST_USER``: :attr:`~integreat_cms.core.settings.EMAIL_HOST_USER`
        * ``DJANGO_EMAIL_PORT``: :attr:`~integreat_cms.core.settings.EMAIL_PORT`

       Cache settings: :attr:`~integreat_cms.core.settings.CACHES`

        * ``DJANGO_REDIS_CACHE``: Whether or not the Redis cache should be enabled
        * ``DJANGO_REDIS_UNIX_SOCKET``: If Redis is enabled and available via a unix socket, set this environment
          variable to the location of the socket, e.g. ``/var/run/redis/redis.sock``.
          Otherwise, the connection falls back to a regular TCP connection on port ``6379``.


Static Files
============

    1. Create root directories for all static files. It's usually good practise to separate code and data, so e.g.
       create the directory ``/var/www/cms/`` with the sub-directories ``static``, ``media``, ``xliff/upload`` and
       ``xliff/download``.

    2. Make sure these directories are directly served by the Apache webserver and not by Django.

    3. Collect static files::

        integreat-cms-cli collectstatic


Database
========

    1. Install a `PostgreSQL <https://www.postgresql.org/>`_ database on your system.
       Installation process varies across different distros (e.g. on `Ubuntu <https://wiki.ubuntuusers.de/PostgreSQL/>`_)

    2. Generate secure credentials and keep them secret

    3. Execute initial migrations::

        integreat-cms-cli migrate


Redis Cache
===========

    1. Install a Redis database on your system which can be used as cache.
       Installation process varies across different distros (e.g. on `Ubuntu <https://wiki.ubuntuusers.de/Redis//>`__).

    2. Set the environment variable ``DJANGO_REDIS_CACHE`` to activate the cache.
       Ideally, the connection is established via a unix socket instead of TCP (Set the environment variable
       ``DJANGO_REDIS_UNIX_SOCKET`` to the location of the unix socket).
