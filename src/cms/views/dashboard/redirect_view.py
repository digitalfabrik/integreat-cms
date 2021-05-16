import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class RedirectView(TemplateView):
    """
    View to select correct dashboard after login:
    Superusers and staff get redirected to the admin dashboard, region users to the region dashboard.
    """

    def get(self, request, *args, **kwargs):
        """
        Redirect to correct dashboard

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user is neither superuser/staff nor a region user

        :return: Redirect user to correct dashboard
        :rtype: ~django.http.HttpResponseRedirect
        """

        user = request.user
        regions = user.profile.regions
        if user.is_superuser or user.is_staff:
            return redirect("admin_dashboard")

        if regions.count() == 1:
            return redirect("dashboard", region_slug=regions.first().slug)

        if regions.exists():
            return redirect("region_selection")

        raise PermissionDenied(f"{user.profile!r} is neither staff not a region user")
