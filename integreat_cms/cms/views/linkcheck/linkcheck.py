import logging
import re

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.base import RedirectView

from linkcheck.models import Link
from cacheops import invalidate_model

from ...utils.filter_links import filter_links
from ...forms.linkcheck.edit_url_form import EditUrlForm

logger = logging.getLogger(__name__)


class LinkListView(ListView):
    """
    View for retrieving a list of links grouped by their state
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "linkcheck/links_by_filter.html"
    #: Designates the name of the variable to use in the context
    #: (see :class:`~django.views.generic.list.MultipleObjectMixin`)
    context_object_name = "filtered_links"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "linkcheck"}
    #: The link edit form
    form = None

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.

        :param queryset: The QuerySet of the filtered links
        :type queryset: ~django.db.models.query.QuerySet

        :return: The pagination number
        :rtype: int
        """
        return int(self.request.GET.get("size", settings.PER_PAGE))

    def get_pagination_params(self):
        """
        Get the urlencoded pagination GET parameters

        :return: The URL params
        :rtype: str
        """
        params = {
            k: v for k, v in self.request.GET.items() if k in (self.page_kwarg, "size")
        }
        print(params)
        if params:
            return f"?{urlencode(params)}"
        return ""

    def get_context_data(self, **kwargs):
        r"""
        Extend context by edit link form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        edit_link_id = self.kwargs.get("link_id")
        if edit_link_id and not self.form:
            link = get_object_or_404(Link, id=edit_link_id)
            self.form = EditUrlForm(initial={"url": link.url})
        context["edit_url_form"] = self.form
        context["pagination_params"] = self.get_pagination_params()
        return context

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

    def get(self, request, *args, **kwargs):
        r"""
        Return the get view and fall back to the last page if the requested page does not exist

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered linkcheck template or a redirect to the last page
        :rtype: ~django.template.response.TemplateResponse or ~django.http.HttpResponseRedirect
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            logger.debug("Redirecting to last page because response was 404")
            # If the page does not exist, use the last page as fallback
            params = {"page": "last"}
            size = request.GET.get("size")
            if size:
                params["size"] = size
            return redirect(f"{request.path}?{urlencode(params)}")

    # pylint: disable-msg=too-many-locals
    def post(self, request, *args, **kwargs):
        r"""
        Applies selected action for selected links

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: Redirect to current linkcheck tab
        :rtype: ~django.http.HttpResponseRedirect
        """
        region_slug = kwargs.get("region_slug")
        edit_link_id = kwargs.get("link_id")
        if edit_link_id:
            old_link = get_object_or_404(Link, id=edit_link_id)
            self.form = EditUrlForm(data=request.POST)
            if self.form.is_valid():
                new_url = self.form.cleaned_data["url"]
                # Get all links in current translations (ignore old versions)
                links = filter_links(region_slug)[0]
                # Get all current translations with the same url
                translations = [
                    item["translation"]
                    for item in links
                    if item["link"].url == old_link.url
                ]
                # Replace the old urls with the new urls in the content
                for translation in translations:
                    translation.content = re.sub(
                        rf"href=[\'\"]{old_link.url.url}[\'\"]",
                        f'href="{new_url}"',
                        translation.content,
                    )
                    # Save translation with replaced content as new version
                    translation.id = None
                    translation.version += 1
                    translation.save()
                messages.success(request, _("URL was successfully replaced"))
            else:
                # Show error messages
                for field in self.form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ": " + _(error))
                # If the form is invalid, render the invalid form
                return super().get(request, *args, **kwargs)

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
        invalidate_model(Link)

        # Keep pagination settings
        return redirect(f"{request.path}{self.get_pagination_params()}")


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
