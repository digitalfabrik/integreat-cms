import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class MatomoApiConfig(AppConfig):
    """
    MatomoApiClient config inheriting the django AppConfig
    """

    #: Full Python path to the application
    name = "integreat_cms.matomo_api"
    #: Human-readable name for the application
    verbose_name = _("Matomo API")
