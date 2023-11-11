from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from django.core.exceptions import BadRequest, Http404, PermissionDenied
    from django.http import HttpRequest
    from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


def render_error_template(context: dict[str, Any]) -> SafeString:
    """
    Render the HTTP error template

    :param context: The context data for the error template
    :return: The rendered template response
    """
    context.update(
        {
            "COMPANY": settings.COMPANY,
            "COMPANY_URL": settings.COMPANY_URL,
            "BRANDING": settings.BRANDING,
            "BRANDING_TITLE": settings.BRANDING_TITLE,
        }
    )
    return render_to_string("error_handler/http_error.html", context)


def handler400(request: HttpRequest, exception: BadRequest) -> HttpResponseBadRequest:
    """
    Render a HTTP 400 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The rendered template response
    """
    context = {
        "request": request,
        "code": 400,
        "title": _("Bad request"),
        "message": _("There was an error in your request."),
    }
    logger.debug(exception)
    return HttpResponseBadRequest(render_error_template(context))


def handler403(
    request: HttpRequest, exception: PermissionDenied
) -> HttpResponseForbidden:
    """
    Render a HTTP 403 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The rendered template response
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("Forbidden"),
        "message": _("You don't have the permission to access this page."),
    }
    logger.debug(exception)
    return HttpResponseForbidden(render_error_template(context))


def handler404(request: HttpRequest, exception: Http404) -> HttpResponseNotFound:
    """
    Render a HTTP 404 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The rendered template response
    """
    context = {
        "request": request,
        "code": 404,
        "title": _("Page not found"),
        "message": _("The page you requested could not be found."),
    }
    logger.debug(exception)
    return HttpResponseNotFound(render_error_template(context))


def handler500(request: HttpRequest) -> HttpResponseServerError:
    """
    Render a HTTP 500 Error code

    :param request: Object representing the user call
    :return: The rendered template response
    """
    context = {
        "request": request,
        "code": 500,
        "title": _("Internal Server Error"),
        "message": _("An unexpected error has occurred."),
    }
    return HttpResponseServerError(render_error_template(context))


def csrf_failure(request: HttpRequest, reason: str) -> HttpResponseForbidden:
    """
    Render a CSRF failure notice

    :param request: Object representing the user call
    :param reason: Description of reason for CSRF failure
    :return: The rendered template response
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("CSRF Error"),
        "message": _("Please try to reload the page."),
    }
    logger.debug(reason)
    return HttpResponseForbidden(render_error_template(context))
