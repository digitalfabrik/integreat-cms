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
    for key in environ:
        if key.startswith("DJANGO_"):
            os.environ[key] = environ[key]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    _application = get_wsgi_application()

    return _application(environ, start_response)
