from django.core.exceptions import PermissionDenied

from .models import Site


def staff_required(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        # superusers and staff have access to this areas
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def region_permission_required(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        # superusers and staff have permissions for all regions
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        region = Site.get_current_site(request)
        if region in user.profile.regions.all():
            return function(request, *args, **kwargs)
        raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
