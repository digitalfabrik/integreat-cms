"""
Celery worker
"""

from __future__ import annotations

import configparser
import os
from typing import TYPE_CHECKING

from celery import Celery
from celery.schedules import crontab
from django.core.management import call_command

if TYPE_CHECKING:
    from typing import Any

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


# @app.task
# def wrapper_create_statistics():
#    """
#    Periodic task to generate region statistics
#    """
#    print("create statistics")
#


@app.task
def wrapper_import_events_from_external_calendars() -> None:
    """
    Periodic task to import events from the external calendars
    """
    call_command("import_events")


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """
    Set up a periodic job to import evens from the external calendars at 0:23 every day
    """
    sender.add_periodic_task(
        crontab(hour=0, minute=23),
        wrapper_import_events_from_external_calendars.s(),
        name="wrapper_import_events_from_external_calendars",
    )
