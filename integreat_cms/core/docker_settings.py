"""
Django settings for different database configuration.
The docker container started in :github-source:`tools/run.sh` exposes the alternative port ``5433``.

All other settings are imported from :mod:`~integreat_cms.core.settings`.

For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

from __future__ import annotations

from .settings import *

#: A dictionary containing the settings for all databases to be used with this Django installation
#: (see :setting:`django:DATABASES`)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "integreat",
        "USER": "integreat",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5433",
    },
}
