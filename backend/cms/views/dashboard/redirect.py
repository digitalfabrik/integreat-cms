"""
View to redirect to the correct dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name='dispatch')
class RedirectView(TemplateView):
    """View class representing redirection to correct dashboard

    Args:
        TemplateView : View inherits from the django TemplateView class

    Returns:
        View : Rendered HTML-Page that will be seen in the CMS-Dashboard
    """

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_staff:
            return redirect('admin_dashboard')
        regions = user.profile.regions
        if regions.exists():
            return redirect('dashboard', region_slug=regions.first().slug)
        raise PermissionDenied
