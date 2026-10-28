"""
WSGI config for backend project.
It exposes the WSGI callable as a module-level variable named ``application``.

:doc:`wsgi:index` (Web Server Gateway Interface) is a simple calling convention for web servers to forward requests to
python frameworks (in our case Django).

For more information on this file, see :doc:`django:howto/deployment/wsgi/index`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.wsgi import get_wsgi_application

from integreat_cms.core.configure import configure_application

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.core.handlers.wsgi import WSGIHandler


def application(environ: dict[str, str], start_response: Callable) -> WSGIHandler:
    """
    This returns the WSGI callable

    :param environ: The environment variables
    :param start_response: A function which starts the response
    :return: The WSGI callable
    """
    configure_application()
    _application = get_wsgi_application()

    return _application(environ, start_response)
