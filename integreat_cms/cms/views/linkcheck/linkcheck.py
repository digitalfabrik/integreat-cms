from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.base import RedirectView

from linkcheck.models import Link

from ...decorators import region_permission_required
from ...utils.filter_links import filter_links


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class LinkListView(ListView):
    """
    View for retrieving a list of links grouped by their state
    """

    template_name = "linkcheck/links_by_filter.html"
    context_object_name = "filtered_links"
    paginate_by = settings.PER_PAGE
    extra_context = {"current_menu_item": "linkcheck"}

    def get_queryset(self):
        """
        Selects all links for the current region
        Finally annotates queryset by the content_type title

        :return: The QuerySet of the filtered links
        :rtype: ~django.db.models.query.QuerySet
        """
        region_slug = self.kwargs.get("region_slug")
        link_filter = self.kwargs.get("link_filter")
        links, count_dict = filter_links(region_slug, link_filter)
        self.extra_context.update(count_dict)
        return links

    def post(self, request, *args, **kwargs):
        r"""
        Applies selected action for selected links

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: Redirct to current linkcheck tab
        :rtype: ~django.http.HttpResponseRedirect
        """
        region_slug = kwargs.get("region_slug")
        link_filter = kwargs.get("link_filter")
        link_ids = request.POST.getlist("selected_ids[]")
        action = request.POST.get("action")
        selected_links = Link.objects.filter(id__in=link_ids)
        if action == "ignore":
            selected_links.update(ignore=True)
            messages.success(request, _("Links were successfully ignored"))
        elif action == "unignore":
            selected_links.update(ignore=False)
            messages.success(request, _("Links were successfully unignored"))
        elif action == "recheck":
            for link in selected_links:
                link.url.check_url(external_recheck_interval=0)
            messages.success(request, _("Links were successfully checked"))
        return redirect("linkcheck", region_slug=region_slug, link_filter=link_filter)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class LinkListRedirectView(RedirectView):
    """
    View for redirecting to main page of the broken link checker
    """

    def get_redirect_url(self, *args, **kwargs):
        r"""
        Retrieve url for redirection

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: url to redirect to
        :rtype: str
        """
        kwargs.update({"link_filter": "invalid"})
        return reverse("linkcheck", kwargs=kwargs)
