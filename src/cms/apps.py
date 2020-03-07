"""
Django related class representing a config of an app
"""
import logging
import sys
from django.conf import settings
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class CmsConfig(AppConfig):
    """
    Class inheriting the django AppConfig
    """

    name = 'cms'

    def ready(self):
        if settings.SECRET_KEY == '-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_' and not settings.DEBUG:
            logger.error("You are running the Integreat CMS in production mode. Change the SECRET_KEY in the settings.py!")
            sys.exit(1)
