*******************
Management Commands
*******************

.. highlight:: bash

Django provides a variety of utility commands to facilitate recurring server maintenance tasks.


Invocation
==========

We renamed ``manage.py`` to :github-source:`integreat-cms-cli <integreat_cms/integreat-cms-cli>`,
so all management commands can be invoked via::

    django-admin COMMAND
    integreat-cms-cli COMMAND

Run ``integreat-cms-cli help`` to get an overview over all available commands.
When developing, you can use the dev tool :github-source:`tools/integreat-cms-cli`
(see :ref:`management-command-tool`) to set all environment variables.


Default Commands
================

See :ref:`ref/django-admin:available commands` for more information about the default options.

Third-party Commands
====================

django-linkcheck
----------------

``findlinks``
~~~~~~~~~~~~~

Scan the content and update the link database.
Make sure to set the environment variable ``INTEGREAT_CMS_LINKCHECK_EXCLUDE_ARCHIVED_PAGES=1``
when you use this command in production to make sure links in archived pages are ignored.

``checklinks``
~~~~~~~~~~~~~~

Check the status of all existing links.


django-debug-toolbar
--------------------

``debugsqlshell``
~~~~~~~~~~~~~~~~~

Print raw SQL queries, see :doc:`django-debug-toolbar:commands`.
