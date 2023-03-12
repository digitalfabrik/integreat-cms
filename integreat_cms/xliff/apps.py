"""
Configuration of XLIFF app
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class XLIFFConfig(AppConfig):
    """
    XLIFF config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name = "integreat_cms.xliff"
    #: Human-readable name for the application
    verbose_name = _("XLIFF")
