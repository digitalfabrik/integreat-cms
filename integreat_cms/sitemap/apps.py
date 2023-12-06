from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


class SitemapConfig(AppConfig):
    """
    This is the basic configuration for the sitemap app
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.sitemap"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("Sitemap")
