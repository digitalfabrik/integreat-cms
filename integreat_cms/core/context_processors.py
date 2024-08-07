"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

from .. import __version__
from ..cms.constants import status

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


def version_processor(request: HttpRequest) -> dict[str, str]:
    """
    This context processor injects the current package version into the template context.

    :param request: The current http request
    :return: The currently installed version of this package
    """
    return {"version": __version__}


def settings_processor(request: HttpRequest) -> dict[str, Any]:
    """
    This context processor injects a few settings into the template context.

    :param request: The current http request
    :return: A few of our settings
    """
    return {
        "FCM_ENABLED": settings.FCM_ENABLED,
        "BRANDING": settings.BRANDING,
        "BRANDING_TITLE": settings.BRANDING_TITLE,
        "WEBAPP_URL": settings.WEBAPP_URL,
        "DEEPL_ENABLED": settings.DEEPL_ENABLED,
        "SUMM_AI_ENABLED": settings.SUMM_AI_ENABLED,
        "TEXTLAB_API_LANGUAGES": settings.TEXTLAB_API_LANGUAGES,
        "TEXTLAB_API_ENABLED": settings.TEXTLAB_API_ENABLED,
        "TEST": settings.TEST,
        "USER_CHAT_TICKET_GROUP": settings.USER_CHAT_TICKET_GROUP,
    }


def constants_processor(request: HttpRequest) -> dict[str, str]:
    """
    This context processor injects some of our constants into the template context.

    :param request: The current http request
    :return: A few of our constants
    """
    return {
        "DRAFT": status.DRAFT,
        "REVIEW": status.REVIEW,
        "AUTO_SAVE": status.AUTO_SAVE,
        "PUBLIC": status.PUBLIC,
    }
