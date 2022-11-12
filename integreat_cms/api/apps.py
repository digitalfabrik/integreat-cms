"""
Meta information about the Integreat CMS API app
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    """
    Configuration parameters for the API app
    """

    #: Full Python path to the application
    name = "integreat_cms.api"
    #: Human-readable name for the application
    verbose_name = _("API")
