"""
Meta information about the Integreat CMS API app
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


class ApiConfig(AppConfig):
    """
    Configuration parameters for the API app
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.api"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("API")
