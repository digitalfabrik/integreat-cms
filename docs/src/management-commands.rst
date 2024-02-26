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
Make sure to set the environment variable ``INTEGREAT_CMS_LINKCHECK_COMMAND_RUNNING=1``
when you use this command in production to make sure links in archived pages are ignored.

``checklinks``
~~~~~~~~~~~~~~

Check the status of all existing links.


django-debug-toolbar
--------------------

``debugsqlshell``
~~~~~~~~~~~~~~~~~

Print raw SQL queries, see :doc:`django-debug-toolbar:commands`.

Custom Commands
===============

integreat-cms
-------------

``duplicate_pages``
~~~~~~~~~~~~~~~~~~~

Duplicate all currently existing pages to make it easier to create production-like data sets::

    integreat-cms-cli duplicate_pages REGION_SLUG

**Arguments:**

* ``REGION_SLUG``: Duplicate all pages of the region with slug ``REGION_SLUG``

.. Note::

    This command inherits from :class:`~integreat_cms.core.management.debug_command.DebugCommand`, so it is only available in debug mode.


``find_large_files``
~~~~~~~~~~~~~~~~~~~~

Find large media files in the CMS::

    integreat-cms-cli find_large_files [--limit LIMIT] [--threshold THRESHOLD]

**Options:**

* ``--limit LIMIT``: Only show the largest ``LIMIT`` files (max 100, defaults to 10)
* ``--threshold THRESHOLD``: Only show files larger than this ``THRESHOLD`` (in MiB, defaults to 3.0)


``find_missing_versions``
~~~~~~~~~~~~~~~~~~~~~~~~~

Find version inconsistencies in the CMS::

    integreat-cms-cli find_missing_versions MODEL

**Arguments:**

* ``MODEL``: The model to check (one of ``page``, ``event``, ``poi``)


``hix_bulk``
~~~~~~~~~~~~

Set the hix value for all pages for which it is missing::

    integreat-cms-cli hix_bulk [REGION_SLUGS ...]

**Arguments:**

* ``REGION_SLUGS``: The slugs of the regions to process, separated by a space. If none are given, every region will be processed


``replace_links``
~~~~~~~~~~~~~~~~~

Search & replace links in the content::

    integreat-cms-cli replace_links SEARCH REPLACE [--region-slug REGION_SLUG] [--username USERNAME] [--commit]

**Arguments:**

* ``SEARCH``: The (partial) URL to search
* ``REPLACE``: The (partial) URL to replace

**Options:**

* ``--region-slug REGION_SLUG``: Only replace links in the region with slug ``REGION_SLUG``
* ``--username USERNAME``: Associate any new created translations with ``USERNAME``
* ``--commit``: Whether changes should be written to the database

``send_push_notifications``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send all due scheduled push notifications::

    integreat-cms-cli send_push_notifications


``fix_internal_links``
~~~~~~~~~~~~~~~~~~~~~~

Search & fix broken internal links in the content::

    integreat-cms-cli fix_internal_links [--region-slug REGION_SLUG] [--username USERNAME] [--commit]

**Options:**

* ``--region-slug REGION_SLUG``: Only fix links in the region with slug ``REGION_SLUG``
* ``--username USERNAME``: Associate any new created translations with ``USERNAME``
* ``--commit``: Whether changes should be written to the database


``summ_ai_bulk``
~~~~~~~~~~~~~~~~

Translate an entire region into Easy German via SUMM.AI::

    integreat-cms-cli summ_ai_bulk REGION_SLUG USERNAME [--initial]

**Arguments:**

* ``REGION_SLUG``: Translate all pages of the region with slug ``REGION_SLUG``
* ``USERNAME``: Associate any new created translations with ``USERNAME``

**Options:**

* ``--initial``: Whether existing translations should not be updated


``reset_mt_budget``
~~~~~~~~~~~~~~~~~~~~~~

Reset MT budget of regions whose renewal month is the current month::

    integreat-cms-cli reset_mt_budget [--force]

**Options:**

* ``--force``: Allow to reset the budget even if it's not the first day of the month


Create new commands
-------------------

When adding new custom commands, you can use the base classes:

:class:`~integreat_cms.core.management.log_command.LogCommand`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A base class for management commands to set the stream handler of the logger to the command's stdout wrapper


:class:`~integreat_cms.core.management.debug_command.DebugCommand`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A base class for management commands which can only be executed in debug mode
