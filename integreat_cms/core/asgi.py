"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

from __future__ import annotations

from django.core.asgi import get_asgi_application

from integreat_cms.core.configure import configure_application

configure_application()
application = get_asgi_application()
