"""
Celery worker
"""

import configparser
import os

from celery import Celery

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
#
# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#    """
#    Set up a periodic job to look for new videos
#    """
#    sender.add_periodic_task(
#        84600,
#        wrapper_create_statistics.s(),
#        name="wrapper_create_statistics",
#    )
