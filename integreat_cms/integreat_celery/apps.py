"""
Set up celery app
"""

from django.apps import AppConfig


class IntegreatCeleryConfig(AppConfig):
    """
    Configuration for Celery
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "integreat_cms.integreat_celery"
