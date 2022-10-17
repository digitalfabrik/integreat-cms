"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""
from django.conf import settings

from .. import __version__
from ..cms.constants import status


# pylint: disable=unused-variable
def version_processor(request):
    """
    This context processor injects the current package version into the template context.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: The currently installed version of this package
    :rtype: dict
    """
    return {"version": __version__}


# pylint: disable=unused-variable
def settings_processor(request):
    """
    This context processor injects a few settings into the template context.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: A few of our settings
    :rtype: dict
    """
    return {
        "FCM_ENABLED": settings.FCM_ENABLED,
        "BRANDING": settings.BRANDING,
        "WEBAPP_URL": settings.WEBAPP_URL,
        "DEEPL_ENABLED": settings.DEEPL_ENABLED,
        "TEXTLAB_API_LANGUAGES": settings.TEXTLAB_API_LANGUAGES,
        "TEXTLAB_API_ENABLED": settings.TEXTLAB_API_ENABLED,
    }


# pylint: disable=unused-variable
def constants_processor(request):
    """
    This context processor injects some of our constants into the template context.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: A few of our constants
    :rtype: dict
    """
    return {
        "DRAFT": status.DRAFT,
        "REVIEW": status.REVIEW,
        "AUTO_SAVE": status.AUTO_SAVE,
        "PUBLIC": status.PUBLIC,
    }
