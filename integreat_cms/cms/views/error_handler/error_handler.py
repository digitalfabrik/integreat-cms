import logging

from django.conf import settings
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def render_error_template(context):
    """
    Render the HTTP error template

    :param context: The context data for the error template
    :type context: dict

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context.update(
        {
            "COMPANY": settings.COMPANY,
            "COMPANY_URL": settings.COMPANY_URL,
            "BRANDING": settings.BRANDING,
        }
    )
    return render_to_string("error_handler/http_error.html", context)


def handler400(request, exception):
    """
    Render a HTTP 400 Error code

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param exception: Exception (unused)
    :type exception: BaseException

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context = {
        "request": request,
        "code": 400,
        "title": _("Bad request"),
        "message": _("There was an error in your request."),
    }
    logger.debug(exception)
    return HttpResponseBadRequest(render_error_template(context))


def handler403(request, exception):
    """
    Render a HTTP 403 Error code

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param exception: Exception (unused)
    :type exception: BaseException

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("Forbidden"),
        "message": _("You don't have the permission to access this page."),
    }
    logger.debug(exception)
    return HttpResponseForbidden(render_error_template(context))


def handler404(request, exception):
    """
    Render a HTTP 404 Error code

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param exception: Exception (unused)
    :type exception: BaseException

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context = {
        "request": request,
        "code": 404,
        "title": _("Page not found"),
        "message": _("The page you requested could not be found."),
    }
    logger.debug(exception)
    return HttpResponseNotFound(render_error_template(context))


def handler500(request):
    """
    Render a HTTP 500 Error code

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context = {
        "request": request,
        "code": 500,
        "title": _("Internal Server Error"),
        "message": _("An unexpected error has occurred."),
    }
    return HttpResponseServerError(render_error_template(context))


def csrf_failure(request, reason):
    """
    Render a CSRF failure notice

    :param request: Object representing the user call
    :type request: ~django.http.HttpRequest

    :param reason: Description of reason for CSRF failure
    :type reason: str

    :return: The rendered template response
    :rtype: ~django.template.response.TemplateResponse
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("CSRF Error"),
        "message": _("Please try to reload the page."),
    }
    logger.debug(reason)
    return HttpResponseForbidden(render_error_template(context))
