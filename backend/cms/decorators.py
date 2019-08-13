from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import Region


def staff_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        user = request.user
        # superusers and staff have access to this areas
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap


def region_permission_required(function):
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
