# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from .settings import *

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASE_DICT = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'integreat',
        'USER': 'integreat',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
