import configparser
import os

import sentry_sdk
from django.conf import settings
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from integreat_cms import __version__


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

    # TODO What does this even do?
    # Read config from environment
    for key, value in os.environ.items():
        if key.startswith("INTEGREAT_CMS_"):
            os.environ[key] = value

    if settings.ENVIRONMENT in ["production", "staging"]:
        sentry_sdk.init(
            dsn="https://626c8f2ed56d7afa46551b9126028bdf@sentry.tuerantuer.org//8",
            environment=settings.ENVIRONMENT,
            release=f"integreat-cms@{__version__}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            integrations=[DjangoIntegration(), CeleryIntegration()],
        )
