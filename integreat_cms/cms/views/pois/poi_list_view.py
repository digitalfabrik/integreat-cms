from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ObjectSearchForm
from ...models import POITranslation
from ..mixins import MachineTranslationContextMixin
from .poi_context_mixin import POIContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_poi"), name="dispatch")
class POIListView(TemplateView, POIContextMixin, MachineTranslationContextMixin):
    """
    View for listing POIs (points of interests)
    """

    #: Template for list of non-archived POIs
    template = "pois/poi_list.html"
    #: Template for list of archived POIs
    template_archived = "pois/poi_list_archived.html"
    #: Whether or not to show archived POIs
    archived = False
    #: The translation model of this list view (used to determine whether machine translations are permitted)
    translation_model = POITranslation

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.pois.poi_list_view.POIListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """
        return self.template_archived if self.archived else self.template

    # pylint: disable=too-many-locals
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render POI list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        # current region
        region = request.region

        # current language
        if language_slug := kwargs.get("language_slug"):
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language:
            return redirect(
                "pois",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _(
                    "Please create at least one language node before creating locations."
                ),
            )
            return redirect(
                "languagetreenodes",
                **{
                    "region_slug": region.slug,
                },
            )

        if not request.user.has_perm("cms.change_poi"):
            messages.warning(
                request, _("You don't have the permission to edit or create locations.")
            )

        pois = region.pois.filter(archived=self.archived)
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            poi_keys = POITranslation.search(region, language_slug, query).values(
                "poi__pk"
            )
            pois = pois.filter(pk__in=poi_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(
            pois.prefetch_translations().order_by("region__slug"), chunk_size
        )
        chunk = request.GET.get("page")
        poi_chunk = paginator.get_page(chunk)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "pois": poi_chunk,
                "archived_count": region.pois.filter(archived=True).count(),
                "language": language,
                "languages": region.active_languages,
                "search_query": query,
                "source_language": region.get_source_language(language.slug),
                "content_type": "locations",
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Apply the query and filter the rendered pois

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
