"""
WSGI config for backend project.
It exposes the WSGI callable as a module-level variable named ``application``.

:doc:`wsgi:index` (Web Server Gateway Interface) is a simple calling convention for web servers to forward requests to
python frameworks (in our case Django).

For more information on this file, see :doc:`howto/deployment/wsgi/index`.
"""

import os
from django.core.wsgi import get_wsgi_application


def application(environ, start_response):
    os.environ["DJANGO_SECRET_KEY"] = environ["DJANGO_SECRET_KEY"]
    os.environ["DJANGO_DEBUG"] = environ["DJANGO_DEBUG"]
    os.environ["DJANGO_BASE_URL"] = environ["DJANGO_BASE_URL"]
    os.environ["DJANGO_WEBAPP_URL"] = environ["DJANGO_WEBAPP_URL"]
    os.environ["DJANGO_DB_HOST"] = environ["DJANGO_DB_HOST"]
    os.environ["DJANGO_DB_PORT"] = environ["DJANGO_DB_PORT"]
    os.environ["DJANGO_DB_USER"] = environ["DJANGO_DB_USER"]
    os.environ["DJANGO_DB_NAME"] = environ["DJANGO_DB_NAME"]
    os.environ["DJANGO_DB_PASSWORD"] = environ["DJANGO_DB_PASSWORD"]
    os.environ["DJANGO_STATIC_ROOT"] = environ["DJANGO_STATIC_ROOT"]
    os.environ["DJANGO_MEDIA_ROOT"] = environ["DJANGO_MEDIA_ROOT"]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    _application = get_wsgi_application()

    return _application(environ, start_response)
