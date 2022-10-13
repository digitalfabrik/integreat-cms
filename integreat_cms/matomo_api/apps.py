import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MatomoApiConfig(AppConfig):
    """
    MatomoApiClient config inheriting the django AppConfig
    """

    name = "integreat_cms.matomo_api"
