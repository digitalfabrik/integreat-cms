***************************
Internationalization (i18n)
***************************

For more detailed information, have a look at the official Django documentation on :doc:`django:topics/i18n/index`.


Hardcoded Strings
=================

Whenever you use hardcoded strings, use english text and encapsulate it with a translation function.

::

    from django.utils.translation import gettext_lazy as _

    string = _('Your string')

.. Note::

    We prefer ``gettext_lazy()`` over ``gettext`` to enable logging the messages in English independent from the user language.


Templates
---------

::

    {% translate "Your string" %}


Translation File
================

.. highlight:: bash

After you finished your changes to the code base, run the following command::

    cd integreat_cms
    integreat-cms-cli makemessages -l de --add-location file

Then, open the file :github-source:`integreat_cms/locale/de/LC_MESSAGES/django.po` and fill in the german translations::

    msgid "Your string"
    msgstr "Deine Zeichenkette"

Apart from German, we also try to support the following additional languages:

* Dutch (:github-source:`integreat_cms/locale/nl/LC_MESSAGES/django.po`)

Since not all of our developers are fluent in those languages, they are not required to be up to date all the time.
However, if you are, feel free to update these additional translation files from time to time be executing::

    cd integreat_cms
    integreat-cms-cli makemessages --all --add-location file

And fill in all translations you can.


Compilation
===========

To actually see the translated strings in the backend UI, compile the django.po file as follows::

    cd integreat_cms
    integreat-cms-cli compilemessages


Developer Tools
===============

To do ``makemessages`` and ``compilemessages`` in one step, use :github-source:`tools/translate.sh`::

    ./tools/translate.sh

If you run into merge/rebase conflicts inside the translation file, use :github-source:`tools/resolve_translation_conflicts.sh`::

    ./tools/resolve_translation_conflicts.sh

If you want to check, whether your translations is up-to-date or if there are any actions required, run :github-source:`tools/check_translations.sh`::

    ./tools/check_translations.sh
