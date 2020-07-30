"""
Django view decorators can be used to restrict the execution of a view function on certain conditions.

For more information, see :doc:`topics/http/decorators`.
"""
import time
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import Region


def staff_required(function):
    """
    This decorator can be used to make sure a view can only be retrieved by users who are either staff or superusers.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        user = request.user
        # superusers and staff have access to this areas
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap


def region_permission_required(function):
    """
    This decorator can be used to make sure a view can only be retrieved by users of the requested region.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        user = request.user
        # superusers and staff have permissions for all regions
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        region = Region.get_current_region(request)
        if region in user.profile.regions.all():
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap


def modify_mfa_authenticated(function):
    """
    This decorator can be used to make sure a user can only modify his 2FA settings when he has a valid 2FA session.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not "modify_mfa_authentication_time" in request.session or request.session[
            "modify_mfa_authentication_time"
        ] < (time.time() - 5 * 60):
            request.session["mfa_redirect_url"] = request.path
            return redirect("user_settings_auth_modify_mfa")
        return function(request, *args, **kwargs)

    return wrap
