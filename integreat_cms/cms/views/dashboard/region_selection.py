import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class RegionSelection(TemplateView):
    """
    View for the region selection
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/region_selection.html"

    def get(self, request, *args, **kwargs):
        r"""
        Redirect to correct dashboard or render the region selection if dashboard cannot be automatically determined

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user is neither superuser/staff nor a region user

        :return: The rendered selection template or a redirect to correct dashboard
        :rtype: ~django.template.response.TemplateResponse or ~django.http.HttpResponseRedirect
        """

        user = request.user
        regions = user.regions
        if user.is_superuser or user.is_staff:
            return redirect("admin_dashboard")

        # If user only has one region, redirect to the dashboard of that region
        if user.distinct_region:
            return redirect("dashboard", region_slug=user.distinct_region.slug)

        if not regions.exists():
            raise PermissionDenied(f"{user!r} is neither staff nor a region user")

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
