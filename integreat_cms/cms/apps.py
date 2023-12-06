from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class CmsConfig(AppConfig):
    """
    This class represents the Django-configuration of the backend.

    See :class:`django.apps.AppConfig` for more information.

    :param name: The name of the app
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.cms"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("CMS")

    # pylint: disable=import-outside-toplevel
    def ready(self) -> None:
        """
        Monkeypatch the checking of internal URLs
        """
        from linkcheck.models import Url

        from .utils.internal_link_checker import check_internal

        Url.check_internal = check_internal
