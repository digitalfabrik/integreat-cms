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



``copy_pois``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Duplicate all POIs of the template region, also all events and contacts if specified, into the target regions

    integreat-cms-cli copy_pois TEMPLATE-SLUG TARGET-SLUG [TARGET-SLUG ...] [--username USERNAME] [--contacts] [--events] [--add-suffix]

**Options:**

* ``--username``: The user as which to create the objects
* ``--contacts``: Whether contacts should be copied too
* ``--events``: Whether events should be copied too
* ``--add-suffix``: Whether the suffix ' (Copy)' should be added to copied objects


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


``import_pois_from_csv``
~~~~~~~~~~~~~~~~~~~~~~~~

Import POIs into the CMS database from a ``.csv`` file::

    integreat-cms-cli import_pois_from_csv CSV_FILE REGION_SLUG USERNAME

**Arguments:**

* ``CSV_FILE``: Import all POIs inside the ``CSV_FILE``
* ``REGION_SLUG``: The ``REGION_SLUG`` of the target region where the POIs should be imported to
* ``USERNAME``: Associate any new created translations with ``USERNAME``

For the format and required columns of the ``.csv`` file, have a look at the :github-source:`tests/core/management/commands/assets/pois_to_import.csv` file.


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


``update_link_text``
~~~~~~~~~~~~~~~~~~~~~~

Update ALL link text of links of the given URL:

    integreat-cms-cli update_link_text --target-url TARGET_URL --new-link-text NEW_LINK_TEXT [--username USERNAME]

**Arguments:**

* ``TARGET_URL``: Update the link text of ALL links of the url ``TARGET_URL``
* ``NEW_LINK_TEXT``: Update the link texts to ``NEW_LINK_TEXT``

**Options:**

* ``USERNAME``: Associate any new created translations with ``USERNAME``


``fetch_page_accesses``
~~~~~~~~~~~~~~~~~~~~~~~

Fetches page accesses from Matomo and store them in the database

    integreat-cms-cli fetch_page_accesses --start-date START_DATE --end-date END_DATE --period PERIOD [--region-slug REGION_SLUG] [--sync SYNC]

**Arguments:**

* ``START_DATE``: Earliest date to fetch, format should be yyyy-mm-dd
* ``END_DATE``: Latest date to fetch, format should be yyyy-mm-dd

**Options:**

* ``REGION_SLUG``: Region to fetch page accesses for, must have statistics activated. If non provided, page accesses from all regions with statistics activated will be fetched
* ``SYNC``: When True page accesses will be fetched as a synchronous process. If not provided or False, page accesses are fetched via celery.


``bulk_replace_page_icons``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Swap media files used as icons on pages according to a CSV file (files need to exist in the media library):

    integreat-cms-cli bulk_replace_page_icons csv

**Arguments:**

* ``csv``: The path to the csv file we want to read the replacements from

**CSV format:**

The file needs to have at least two columns. The header and any additional columns are ignored.
The paths describe the path of the file *on disk* on the server (relative to the root location where all media is stored), not the "virtual" one in the media library.
This path is also used directly as part of the URL that clients use to retrieve the file contents.
That full URL can also be specified so and will be stripped out automatically.

======================================================================================================  =========================================================================  ========================================
Source path                                                                                             Target path                                                                Comment
======================================================================================================  =========================================================================  ========================================
``https://cms.integreat-app.de/media/sites/83/2015/09/phone-handset_icon-icons.com_48252-300x300.png``  ``/sites/0/2025/08/phone_85134.svg``                                       this is a comment that will be discarded
``admin.integreat-app.de/media/sites/83/2016/04/calendar60.png``                                        ``https://cms.integreat-app.de/media/sites/0/2025/08/calendar_26397.svg``  etc.
======================================================================================================  =========================================================================  ========================================


Create new commands
-------------------

When adding new custom commands, you can use the base classes:

:class:`~integreat_cms.core.management.log_command.LogCommand`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A base class for management commands to set the stream handler of the logger to the command's stdout wrapper


:class:`~integreat_cms.core.management.debug_command.DebugCommand`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A base class for management commands which can only be executed in debug mode
