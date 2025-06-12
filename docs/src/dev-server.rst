******************
Development Server
******************


Database
========

Two different types of local database servers are supported:

* `Docker <https://www.docker.com/>`_ container (recommended)

  - Will be automatically created and started if you use the ``run.sh`` script without a local server running on port 5432
  - Uses the alternate port 5433 (configured at :mod:`~integreat_cms.core.docker_settings`)
  - Requires permissions to connect to the docker daemon:

    + If the user is in the ``docker`` group, no ``sudo`` is required
    + Otherwise, the server will restart itself with elevated permissions for all docker commands
      (the dev server will still run as the user who invoked ``sudo``)

* Native `PostgreSQL <https://www.postgresql.org/>`_ installation on your system

  - Install and run manually before starting the local webserver
  - Installation process varies across different distros (e.g. on `Ubuntu <https://wiki.ubuntuusers.de/PostgreSQL/>`_)
  - Configuration: (see :mod:`~integreat_cms.core.settings`)

    + Port: ``5432``
    + Database: ``integreat``
    + Username: ``integreat``
    + Password: ``password``

  - Set the permissions to create a database manually (needed for tests) inside the PostrgreSQL shell with ``ALTER ROLE integreat CREATE_DB``

.. Note::

    If you want to remove all contents of your database, use :github-source:`tools/prune_database.sh`.


Webserver
=========

Run the inbuilt local webserver with :github-source:`tools/run.sh`::

    ./tools/run.sh

This is a convenience script which also performs the following actions:

* Compile and minify CSS
* Starting a webpack dev server that compiles js and css code
* Regenerate and compile translation file
* Migrate database

If you want to speed up this process and don't need the extra functionality, you might also use::

    ./tools/run.sh --fast

or directly::

    integreat-cms-cli runserver localhost:8000 --settings=integreat_cms.core.docker_settings

or::

    integreat-cms-cli runserver localhost:8000

Depending on your local database server.

After that, open your browser and navigate to http://localhost:8000/.

.. Note::

    If you want to use another port than ``8000``, start the server with ``integreat-cms-cli`` and choose another port, or edit :github-source:`tools/_functions.sh`.
