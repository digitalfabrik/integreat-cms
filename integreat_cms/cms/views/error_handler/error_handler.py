from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from django.core.exceptions import BadRequest, Http404, PermissionDenied
    from django.http import HttpRequest
    from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


def is_api_request(request: HttpRequest) -> bool:
    """
    Check whether the given request is directed at the API

    :param request: Object representing the user call
    :return: Whether the request belongs to the API namespace
    """
    if request.resolver_match:
        return request.resolver_match.app_name == "api"
    # If the url could not be resolved at all, fall back to the url prefix of the API
    return request.path.startswith("/api/")


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
        },
    )
    return render_to_string("error_handler/http_error.html", context)


def _render_error_response(context: dict[str, Any]) -> HttpResponse:
    """
    Render the HTTP error response

    Requests to the API always return JSON, all other requests return the rendered HTML error template.

    :param context: The context data for the error
    :return: The error response
    """
    if is_api_request(context["request"]):
        return JsonResponse({"error": context["message"]}, status=context["code"])
    return HttpResponse(render_error_template(context), status=context["code"])


def handler400(request: HttpRequest, exception: BadRequest) -> HttpResponse:
    """
    Render a HTTP 400 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The error response
    """
    context = {
        "request": request,
        "code": 400,
        "title": _("Bad request"),
        "message": _("There was an error in your request."),
    }
    logger.debug(exception)
    return _render_error_response(context)


def handler403(
    request: HttpRequest,
    exception: PermissionDenied,
) -> HttpResponse:
    """
    Render a HTTP 403 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The error response
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("Forbidden"),
        "message": _("You don't have the permission to access this page."),
    }
    logger.debug(exception)
    return _render_error_response(context)


def handler404(request: HttpRequest, exception: Http404) -> HttpResponse:
    """
    Render a HTTP 404 Error code

    :param request: Object representing the user call
    :param exception: Exception (unused)
    :return: The error response
    """
    context = {
        "request": request,
        "code": 404,
        "title": _("Page not found"),
        "message": _("The page you requested could not be found."),
    }
    logger.debug(exception)
    return _render_error_response(context)


def handler500(request: HttpRequest) -> HttpResponse:
    """
    Render a HTTP 500 Error code

    :param request: Object representing the user call
    :return: The error response
    """
    context = {
        "request": request,
        "code": 500,
        "title": _("Internal Server Error"),
        "message": _("An unexpected error has occurred."),
    }
    return _render_error_response(context)


def csrf_failure(request: HttpRequest, reason: str) -> HttpResponse:
    """
    Render a CSRF failure notice

    :param request: Object representing the user call
    :param reason: Description of reason for CSRF failure
    :return: The error response
    """
    context = {
        "request": request,
        "code": 403,
        "title": _("CSRF Error"),
        "message": _("Please try to reload the page."),
    }
    logger.debug(reason)
    return _render_error_response(context)
