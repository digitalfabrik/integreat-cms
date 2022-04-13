import logging

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import resolve

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class AccessControlMiddleware:
    """
    Middleware class that performs a basic access control. For urls that are whitelisted (see
    :attr:`~integreat_cms.core.middleware.access_control_middleware.AccessControlMiddleware.whitelist`), no additional
    rules are enforced.
    For all other urls, the user has to be either superuser or staff, or needs access to the current region.
    """

    #: The namespaces that are whitelisted and don't require access control
    whitelist = [
        "api",
        "public",
        "sitemap",
        "i18n",
        "media_files",
        "pdf_files",
        "xliff_files",
    ]

    def __init__(self, get_response):
        """
        Initialize the middleware for the current view

        :param get_response: A callable to get the response for the current request
        :type get_response: ~collections.abc.Callable
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Call the middleware for the current request

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the permission to access the requested area

        :return: The response after the region has been added to the request variable
        :rtype: ~django.http.HttpResponse
        """
        # Resolve current url
        resolver_match = resolve(request.path)
        # Only enforce access control if the namespace of this url is not whitelisted
        if resolver_match.app_name not in self.whitelist:
            # If the user isn't authenticated at all, don't throw an error, but just redirect the login form
            if not request.user.is_authenticated:
                return redirect_to_login(request.path)
            # If the user is authenticated, but does not provide access to the requested area, raise an exception
            if not (
                request.user.is_superuser
                or request.user.is_staff
                or request.region in request.user.regions.all()
            ):
                requested_area = (
                    repr(request.region) if request.region else "the staff area"
                )
                raise PermissionDenied(
                    f"{request.user!r} does not have the permission to access {requested_area}"
                )
        # Continue with the request
        return self.get_response(request)
