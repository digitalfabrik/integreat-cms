from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SitemapConfig(AppConfig):
    """
    This is the basic configuration for the sitemap app
    """

    #: Full Python path to the application
    name = "integreat_cms.sitemap"
    #: Human-readable name for the application
    verbose_name = _("Sitemap")
