"""
Celery worker

Usage example:

.. code-block:: python

    @app.task
    def wrapper_create_statistics():
       print("create statistics")


    @app.on_after_configure.connect
    def setup_periodic_tasks(sender, **kwargs):
       sender.add_periodic_task(
           84600,
           wrapper_create_statistics.s(),
           name="wrapper_create_statistics",
       )

"""

from __future__ import annotations

import configparser
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import sentry_sdk
from celery import Celery, signals
from celery.schedules import crontab
from celery.signals import setup_logging
from django.conf import settings
from django.core.management import call_command
from sentry_sdk.integrations.celery import CeleryIntegration

from integreat_cms import __version__

if TYPE_CHECKING:
    from typing import Any


@setup_logging.connect
def config_loggers(*args: Any, **kwags: Any) -> None:
    from logging.config import dictConfig

    dictConfig(settings.LOGGING)


# Read config from config file
config = configparser.ConfigParser(interpolation=None)
config.read("/etc/integreat-cms.ini")

for section in config.sections():
    for KEY, VALUE in config.items(section):
        os.environ.setdefault(f"INTEGREAT_CMS_{KEY.upper()}", VALUE)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "integreat_cms.core.settings")

app = Celery("celery_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.task_routes = {
    "integreat_cms.cms.views.statistics.statistics_actions": {"queue": "statistics"},
    "integreat_cms.api.v3.chat.utils.chat_bot.*": {"queue": "chat"},
}


@signals.celeryd_init.connect
def init_sentry(**_kwargs: Any) -> None:
    if settings.ENVIRONMENT in ["production", "staging"]:
        sentry_sdk.init(
            dsn="https://1c1f99e0448508351c4f5ec6770be414@sentry.tuerantuer.org//10",
            environment=settings.ENVIRONMENT,
            release=f"integreat-cms@{__version__}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            send_default_pii=False,
            integrations=[CeleryIntegration()],
        )
        sentry_sdk.set_tag("component", "celery-worker")


@app.task
def wrapper_import_events_from_external_calendars() -> None:
    """
    Periodic task to import events from the external calendars
    """
    call_command("import_events")


@app.task
def wrapper_fetch_page_accesses() -> None:
    """
    Periodic task to fetch page accesses of the previous day from Matomo
    """
    fetch_date = datetime.today() - timedelta(days=1)
    fetch_date_str = fetch_date.strftime("%Y-%m-%d")
    call_command(
        "fetch_page_accesses",
        start_date=fetch_date_str,
        end_date=fetch_date_str,
    )


@app.task
def wrapper_import_external_news() -> None:
    """
    Periodic task to import news from Tü News
    """
    call_command("import_external_news")


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """
    Set up periodic jobs
    """
    sender.add_periodic_task(
        crontab(hour=0, minute=23),
        wrapper_import_events_from_external_calendars.s(),
        name="wrapper_import_events_from_external_calendars",
    )

    sender.add_periodic_task(
        crontab(hour=0, minute=30),
        wrapper_fetch_page_accesses.s(),
        name="wrapper_fetch_page_accesses",
    )

    sender.add_periodic_task(
        crontab(hour=0, minute=40),
        wrapper_import_external_news.s(),
        name="wrapper_import_external_news",
    )
