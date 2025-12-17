"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

from __future__ import annotations

import configparser
import os

from django.core.asgi import get_asgi_application


def configure_application() -> None:
    """
    Configure settings based on config file and environment variables
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "integreat_cms.core.settings")

    # Read config from config file
    config = configparser.ConfigParser(interpolation=None)
    config.read("/etc/integreat-cms.ini")
    for section in config.sections():
        for KEY, VALUE in config.items(section):
            os.environ.setdefault(f"INTEGREAT_CMS_{KEY.upper()}", VALUE)

    # Read config from environment
    for key, value in os.environ.items():
        if key.startswith("INTEGREAT_CMS_"):
            os.environ[key] = value


configure_application()
application = get_asgi_application()
