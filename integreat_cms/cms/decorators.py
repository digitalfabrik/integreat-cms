"""
Django view decorators can be used to restrict the execution of a view function on certain conditions.

For more information, see :doc:`django:topics/http/decorators`.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import HttpRequest, HttpResponse
    from django.utils.functional import SimpleLazyObject


def permission_required(permission: str) -> Callable:
    """
    Decorator for views that checks whether a user has a particular permission enabled.
    If not, the PermissionDenied exception is raised.

    :param permission: The required permission
    :return: The decorated function
    """

    def check_permission(user: SimpleLazyObject) -> bool:
        """
        This function checks the permission of a user

        :param user: The user, that is checked
        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the given permission

        :return: Whether this account has the permission or not
        """

        if user.has_perm(permission):
            return True
        raise PermissionDenied(f"{user!r} does not have the permission {permission!r}")

    return user_passes_test(check_permission)


def region_permission_required(function: Callable) -> Callable:
    """
    This decorator can be used to make sure a view can only be retrieved by users of the requested region.

    :param function: The view function which should be protected
    :return: The decorated function
    """

    @wraps(function)
    def wrap(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        The inner function for this decorator

        :param request: Django request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs
        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the permission to access the region

        :return: the decorated function
        """
        user = request.user
        # superusers and staff have permissions for all regions
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        if request.region in user.regions.all():
            return function(request, *args, **kwargs)
        raise PermissionDenied(
            f"{user!r} does not have the permission to access {request.region!r}"
        )

    return wrap


def modify_mfa_authenticated(function: Callable) -> Callable:
    """
    This decorator can be used to make sure a user can only modify his 2FA settings when he has a valid 2FA session.

    :param function: The view function which should be protected
    :return: The decorated function
    """

    @wraps(function)
    def wrap(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        The inner function for this decorator

        :param request: Django request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs
        :return: the decorated function
        """
        if "modify_mfa_authentication_time" not in request.session or request.session[
            "modify_mfa_authentication_time"
        ] < (time.time() - 5 * 60):
            request.session["mfa_redirect_url"] = request.path
            region_kwargs = (
                {"region_slug": request.region.slug} if request.region else {}
            )
            return redirect("authenticate_modify_mfa", **region_kwargs)
        return function(request, *args, **kwargs)

    return wrap
