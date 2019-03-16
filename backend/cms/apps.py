"""
Django related class representing a config of an app
"""
from django.apps import AppConfig


class CmsConfig(AppConfig):
    """
    Class inheriting the django AppConfig
    """

    name = 'cms'
