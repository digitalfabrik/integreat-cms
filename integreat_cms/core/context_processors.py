"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""
from django.conf import settings
from integreat_cms import __version__


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
    }


# pylint: disable=unused-variable
def branding_processor(request):
    """
    This context processor injects the setting :attr:`~integreat_cms.core.settings.BRANDING` into the template context.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: The currently installed version of this package
    :rtype: dict
    """
    return {"BRANDING": settings.BRANDING}
