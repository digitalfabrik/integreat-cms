# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from django.core.exceptions import ImproperlyConfigured

from .settings import *


def get_env_value(env_variable):
    try:
        return os.environ[env_variable]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(env_variable)
        raise ImproperlyConfigured(error_msg)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'djangojenkins',
        'USER': get_env_value('CMS_DJANGO_DATABASE_USER'),
        'PASSWORD': get_env_value('CMS_DJANGO_DATABASE_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3333',
        'TEST': {
            'NAME': 'djangojenkins_test',
        },
    }
}
