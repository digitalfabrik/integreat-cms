"""
Django settings for the Sphinx documentation builder.
All configuration is imported from :mod:`~integreat_cms.core.settings` except it sets :attr:`USE_I18N` to ``False`` to
make sure the documentation is not partially translated.

For more information on this file, see :doc:`topics/settings`.
For the full list of settings and their values, see :doc:`ref/settings`.
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from .settings import *


#: Set a dummy secret key for documentation build even if it's not in debug mode
SECRET_KEY = "dummy"

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`topics/i18n/index`)
USE_I18N = False

# Remove cacheops during documentation build because it changes related names
if "cacheops" in INSTALLED_APPS:
    INSTALLED_APPS.remove("cacheops")
