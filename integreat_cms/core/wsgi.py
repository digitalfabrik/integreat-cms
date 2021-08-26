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
    """
    This returns the WSGI callable

    :param environ: The environment variables
    :type environ: dict

    :param start_response: A function which starts the response
    :type start_response: ~collections.abc.Callable

    :return: The WSGI callable
    :rtype: ~django.core.handlers.WSGIHandler
    """
    for key in environ:
        if key.startswith("INTEGREAT_CMS_"):
            os.environ[key] = environ[key]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "integreat_cms.core.settings")
    _application = get_wsgi_application()

    return _application(environ, start_response)
