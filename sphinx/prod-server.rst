*****************
Production Server
*****************

.. highlight:: bash

.. Attention::

    This guide is not the final deployment workflow and will probably change in the near future.


Database
========

Install a `PostgreSQL <https://www.postgresql.org/>`_ database on your system

    - Installation process varies across different distros (e.g. on `Ubuntu <https://wiki.ubuntuusers.de/PostgreSQL/>`_)
    - Generate secure credentials and keep them secret


Webserver
=========

    1. Set up an `Apache2 server with mod_wsgi <https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/modwsgi/>`_.
       You can use the :github-source:`example-configs/apache2-integreat-vhost.conf`.
    2. Set the following environment variables in the Apache2 config to ensure a safe and secure service:

        * ``DJANGO_SECRET_KEY``: :attr:`~backend.settings.SECRET_KEY`
        * ``DJANGO_DEBUG``: :attr:`~backend.settings.DEBUG`
        * ``DJANGO_LOGFILE``: :attr:`~backend.settings.LOGFILE`
        * ``DJANGO_WEBAPP_URL``: :attr:`~backend.settings.WEBAPP_URL`
        * ``DJANGO_MATOMO_URL``: :attr:`~backend.settings.MATOMO_URL`
        * ``DJANGO_BASE_URL``: :attr:`~backend.settings.BASE_URL`
        * ``DJANGO_STATIC_ROOT``: :attr:`~backend.settings.STATIC_ROOT`
        * ``DJANGO_MEDIA_ROOT``: :attr:`~backend.settings.MEDIA_ROOT`

       Database settings: :attr:`~backend.settings.DATABASES`

        * ``DJANGO_DB_HOST``
        * ``DJANGO_DB_NAME``
        * ``DJANGO_DB_PASSWORD``
        * ``DJANGO_DB_USER``
        * ``DJANGO_DB_PORT``

       Email settings:

        * ``DJANGO_EMAIL_HOST``: :attr:`~backend.settings.EMAIL_HOST`
        * ``DJANGO_EMAIL_HOST_PASSWORD``: :attr:`~backend.settings.EMAIL_HOST_PASSWORD`
        * ``DJANGO_EMAIL_HOST_USER``: :attr:`~backend.settings.EMAIL_HOST_USER`
        * ``DJANGO_EMAIL_PORT``: :attr:`~backend.settings.EMAIL_PORT`

       Cache settings: :attr:`~backend.settings.CACHES`

        * ``DJANGO_REDIS_CACHE``: Whether or not the Redis cache should be enabled
        * ``DJANGO_REDIS_UNIX_SOCKET``: If Redis is enabled and available via a unix socket, set this environment
          variable to the location of the socket, e.g. ``/var/run/redis/redis.sock``.
          Otherwise, the connection falls back to a regular TCP connection on port ``6379``.

    3. Clone this repo into ``/opt/``.
    4. Edit the :github-source:`src/backend/settings.py` if a setting you want to change is not configurable via
       environment variables.
    5. Create a virtual environment::

        cd /opt/integreat-cms
        python3 -m venv .venv
        source .venv/bin/activate

    6. Use setuptools to install: ``python3 setup.py develop``. It is also possible to use the ``install`` parameter,
       but this requires changes to the ``wsgi.py`` path in the Apache2 config.
    7. Run the database migrations: ``integreat-cms-cli migrate``
    8. Collect static files: ``integreat-cms-cli collectstatic``


Redis Cache
===========

Install a Redis database on your system which can be used as cache.

    * Installation process varies across different distros (e.g. on `Ubuntu <https://wiki.ubuntuusers.de/Redis//>`__).
    * Set the environment variable ``DJANGO_REDIS_CACHE`` to activate the cache
    * Ideally, the connection is established via a unix socket instead of TCP (Set the environment variable
      ``DJANGO_REDIS_UNIX_SOCKET`` to the location of the unix socket).
