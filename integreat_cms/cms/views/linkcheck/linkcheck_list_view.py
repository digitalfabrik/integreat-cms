from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from cacheops import invalidate_model
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from linkcheck.models import Link, Url

from ...decorators import permission_required
from ...forms.linkcheck.edit_url_form import EditUrlForm
from ...utils.linkcheck_utils import filter_urls, get_urls

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse
    from django.template.response import TemplateResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_broken_links"), name="dispatch")
class LinkcheckListView(ListView):
    """
    View for retrieving a list of urls grouped by their state
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name: str = "linkcheck/links_by_filter.html"
    #: Designates the name of the variable to use in the context
    #: (see :class:`~django.views.generic.list.MultipleObjectMixin`)
    context_object_name: str = "filtered_urls"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context: dict[str, str | int] = {
        "current_menu_item": "linkcheck",
        "LINKCHECK_EMAIL_ENABLED": settings.LINKCHECK_EMAIL_ENABLED,
        "LINKCHECK_PHONE_ENABLED": settings.LINKCHECK_PHONE_ENABLED,
    }
    #: The currently edited instance
    instance: Url | None = None
    #: The link edit form
    form: EditUrlForm | None = None

    def get_paginate_by(self, queryset: list[Url]) -> int:
        """
        Get the number of items to paginate by, or ``None`` for no pagination.

        :param queryset: The QuerySet of the filtered urls
        :return: The pagination number
        """
        return int(self.request.GET.get("size", settings.PER_PAGE))

    def get_pagination_params(self) -> str:
        """
        Get the urlencoded pagination GET parameters

        :return: The URL params
        """
        params = {
            k: v for k, v in self.request.GET.items() if k in (self.page_kwarg, "size")
        }
        return f"?{urlencode(params)}" if params else ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Extend context by edit url form

        :param \**kwargs: The supplied keyword arguments
        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["edit_url_form"] = self.form
        context["pagination_params"] = self.get_pagination_params()
        return context

    def get_queryset(self) -> list[Url]:
        """
        Selects all urls for the current region
        Finally annotates queryset by the content_type title

        :return: The QuerySet of the filtered urls
        """
        urls, count_dict = filter_urls(
            self.kwargs.get("region_slug"),
            self.kwargs.get("url_filter"),
            prefetch_links=True,
        )
        self.extra_context.update(count_dict)
        return urls

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Dispatch the view to either get() or post()
        """
        if edit_url_id := kwargs.pop("url_id", None):
            region = request.region.slug if request.region else None
            try:
                self.instance = get_urls(
                    region,
                    url_ids=[edit_url_id],
                    prefetch_links=True,
                )[0]
            except IndexError as e:
                raise Http404("This URL does not exist") from e
            if request.POST:
                form_kwargs = {"data": request.POST}
            else:
                form_kwargs = {"initial": {"url": self.instance}}
            self.form = EditUrlForm(**form_kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> TemplateResponse:
        r"""
        Return the get view and fall back to the last page if the requested page does not exist

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: When the view returns a 404 and already requests the last page

        :return: The rendered linkcheck template or a redirect to the last page
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # If already the last page was requested, raise the error
            if request.GET.get("page") == "last":
                raise
            # If the page does not exist, use the last page as fallback
            logger.debug("Redirecting to last page because response was 404")
            params = {"page": "last"}
            if size := request.GET.get("size"):
                params["size"] = size
            return redirect(f"{request.path}?{urlencode(params)}")

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Applies selected action for selected urls

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.http.Http404: HTTP status 404 if the edited URL does not exist

        :return: Redirect to current linkcheck tab
        """
        if self.form:
            if self.form.is_valid():
                if TYPE_CHECKING:
                    assert self.instance
                new_url = self.form.cleaned_data["url"]
                # Get all current contents with the same url
                links = (
                    self.instance.regions_links
                    if self.request.region
                    else self.instance.links.all()
                )
                contents = {link.content_object for link in links}
                # Replace the old urls with the new urls in the content
                for content in contents:
                    content.replace_urls(
                        {self.instance.url: new_url},
                        request.user,
                        True,
                    )

                if new_url.startswith("mailto:"):
                    messages.success(request, _("Email link was successfully replaced"))
                elif new_url.startswith("tel:"):
                    messages.success(
                        request,
                        _("Phone number link was successfully replaced"),
                    )
                else:
                    messages.success(request, _("URL was successfully replaced"))
                # Add short delay to allow post_save signals to finish (to keep existing URL objects when deleting the old links)
                time.sleep(0.5)
            else:
                # Show error messages
                for field in self.form:
                    for error in field.errors:
                        messages.error(request, _(field.label) + ": " + _(error))
                # If the form is invalid, render the invalid form
                return super().get(request, *args, **kwargs)

        if action := request.POST.get("action"):
            region_slug = request.region.slug if request.region else None
            selected_urls = get_urls(
                region_slug=region_slug,
                url_ids=request.POST.getlist("selected_ids[]"),
                prefetch_links=True,
            )

            if action == "ignore":
                for url in selected_urls:
                    link_ids = (
                        [link.id for link in url.regions_links]
                        if region_slug
                        else url.links.all()
                    )
                    Link.objects.filter(id__in=link_ids).update(ignore=True)
                messages.success(
                    request,
                    _("Links were successfully marked as verified"),
                )
            elif action == "unignore":
                for url in selected_urls:
                    link_ids = (
                        [link.id for link in url.regions_links]
                        if region_slug
                        else url.links.all()
                    )
                    Link.objects.filter(id__in=link_ids).update(ignore=False)
                messages.success(request, _("Verification was revoked for the links"))
            elif action == "recheck":
                for url in selected_urls:
                    url.check_url(external_recheck_interval=0)
                messages.success(request, _("Links were successfully checked"))
                # Add short delay to allow rechecking to be finished when page reloads
                time.sleep(1)

        invalidate_model(Link)
        invalidate_model(Url)
        url_for_current_region = reverse("linkcheck", kwargs=kwargs)
        # Keep pagination settings
        return redirect(f"{url_for_current_region}{self.get_pagination_params()}")
