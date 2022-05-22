import logging
import time

from copy import deepcopy
from functools import partial
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import gettext as _
from django.views.generic import ListView

from lxml.html import rewrite_links

from linkcheck import update_lock
from linkcheck.models import Link, Url
from cacheops import invalidate_model

from ...utils.linkcheck_utils import filter_urls, get_urls
from ...forms.linkcheck.edit_url_form import EditUrlForm

logger = logging.getLogger(__name__)


class LinkcheckListView(ListView):
    """
    View for retrieving a list of urls grouped by their state
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "linkcheck/links_by_filter.html"
    #: Designates the name of the variable to use in the context
    #: (see :class:`~django.views.generic.list.MultipleObjectMixin`)
    context_object_name = "filtered_urls"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "linkcheck"}
    #: The link edit form
    form = None

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.

        :param queryset: The QuerySet of the filtered urls
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
        Extend context by edit url form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        edit_url_id = self.kwargs.get("url_id")
        if edit_url_id and not self.form:
            url = get_object_or_404(Url, id=edit_url_id)
            self.form = EditUrlForm(initial={"url": url})
        context["edit_url_form"] = self.form
        context["pagination_params"] = self.get_pagination_params()
        return context

    def get_queryset(self):
        """
        Selects all urls for the current region
        Finally annotates queryset by the content_type title

        :return: The QuerySet of the filtered urls
        :rtype: ~django.db.models.query.QuerySet
        """
        urls, count_dict = filter_urls(
            self.kwargs.get("region_slug"), self.kwargs.get("url_filter")
        )
        self.extra_context.update(count_dict)
        return urls

    def get(self, request, *args, **kwargs):
        r"""
        Return the get view and fall back to the last page if the requested page does not exist

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.http.Http404: When the view returns a 404 and already requests the last page

        :return: The rendered linkcheck template or a redirect to the last page
        :rtype: ~django.template.response.TemplateResponse or ~django.http.HttpResponseRedirect
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404 as e:
            # If already the last page was requested, raise the error
            if request.GET.get("page") == "last":
                raise (e)
            # If the page does not exist, use the last page as fallback
            logger.debug("Redirecting to last page because response was 404")
            params = {"page": "last"}
            size = request.GET.get("size")
            if size:
                params["size"] = size
            return redirect(f"{request.path}?{urlencode(params)}")

    # pylint: disable-msg=too-many-locals,too-many-branches
    def post(self, request, *args, **kwargs):
        r"""
        Applies selected action for selected urls

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.http.Http404: HTTP status 404 if the edited URL does not exist

        :return: Redirect to current linkcheck tab
        :rtype: ~django.http.HttpResponseRedirect
        """
        edit_url_id = kwargs.pop("url_id", None)
        if edit_url_id:
            try:
                old_url = get_urls(
                    region_slug=request.region.slug, url_ids=[edit_url_id]
                )[0]
            except IndexError as e:
                raise Http404("This URL does not exist") from e
            self.form = EditUrlForm(data=request.POST)
            if self.form.is_valid():
                new_url = self.form.cleaned_data["url"]
                # Get all current translations with the same url
                translations = {link.content_object for link in old_url.region_links}
                # Replace the old urls with the new urls in the content
                for translation in translations:
                    new_translation = deepcopy(translation)
                    # Replace link in translation
                    logger.debug("Replacing links of %r", new_translation)
                    new_translation.content = rewrite_links(
                        new_translation.content,
                        partial(self.replace_link, old_url.url, new_url),
                    )
                    # Save translation with replaced content as new minor version
                    new_translation.id = None
                    new_translation.version += 1
                    new_translation.minor_edit = True
                    new_translation.save()
                messages.success(request, _("URL was successfully replaced"))
                # Add short delay to allow post_save signals to finish (to keep existing URL objects when deleting the old links)
                time.sleep(0.5)
                # Acquire linkcheck lock to avoid race conditions between post_save signal and links.delete()
                with update_lock:
                    for translation in translations:
                        # Delete now outdated link objects
                        translation.links.all().delete()
                # Add short delay to allow rechecking to be finished when page reloads
                time.sleep(0.5)
            else:
                # Show error messages
                for field in self.form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ": " + _(error))
                # If the form is invalid, render the invalid form
                return super().get(request, *args, **kwargs)

        action = request.POST.get("action")
        selected_urls = get_urls(
            region_slug=request.region.slug,
            url_ids=request.POST.getlist("selected_ids[]"),
            prefetch_content_objects=False,
        )

        if action == "ignore":
            for url in selected_urls:
                Link.objects.filter(
                    id__in=[link.id for link in url.region_links]
                ).update(ignore=True)
            messages.success(request, _("Links were successfully ignored"))
        elif action == "unignore":
            for url in selected_urls:
                Link.objects.filter(
                    id__in=[link.id for link in url.region_links]
                ).update(ignore=False)
            messages.success(request, _("Links were successfully unignored"))
        elif action == "recheck":
            for url in selected_urls:
                url.check_url(external_recheck_interval=0)
            messages.success(request, _("Links were successfully checked"))
            # Add short delay to allow rechecking to be finished when page reloads
            time.sleep(1)
        invalidate_model(Link)
        invalidate_model(Url)
        linkcheck_url = reverse("linkcheck", kwargs=kwargs)
        # Keep pagination settings
        return redirect(f"{linkcheck_url}{self.get_pagination_params()}")

    @staticmethod
    def replace_link(old_url, new_url, link):
        """
        Replace the URL of a link

        :param old_url: The old URL to be replaced
        :type old_url: str

        :param new_url: The new URL
        :type new_url: str

        :param link: The input link
        :type link: str

        :return: The replaced link
        :rtype: str
        """
        if link == old_url:
            logger.debug("Replacing %r with %r", old_url, new_url)
            return new_url
        return link
