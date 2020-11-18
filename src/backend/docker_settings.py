"""
Django settings for different database configuration.
The docker container started in :github-source:`dev-tools/run.sh` exposes the alternative port ``5433``.

For more information on this file, see :doc:`topics/settings`.
For the full list of settings and their values, see :doc:`ref/settings`.
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "integreat",
        "USER": "integreat",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5433",
    }
}
