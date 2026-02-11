from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ObjectSearchForm
from ...models import POITranslation
from ..mixins import FilterSortMixin, MachineTranslationContextMixin, PaginationMixin
from .poi_context_mixin import POIContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_poi"), name="dispatch")
class POIListView(
    TemplateView,
    POIContextMixin,
    MachineTranslationContextMixin,
    FilterSortMixin,
    PaginationMixin,
):
    """
    View for listing POIs (points of interests)
    """

    #: Template for list of non-archived and archived POIs
    template_name = "pois/poi_list.html"
    #: Whether or not to show archived POIs
    archived = False
    #: The translation model of this list view (used to determine whether machine translations are permitted)
    translation_model = POITranslation
    filter_form_class = ObjectSearchForm

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
                    "Please create at least one language node before creating locations.",
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
                request,
                _("You don't have the permission to edit or create locations."),
            )

        pois = region.pois.filter(archived=self.archived)
        query = None

        pois = self.get_filtered_sorted_queryset(pois)
        search_form = self.filter_form_class(request.GET)
        if search_form.is_valid():
            # we have to include additional search results here
            # because we search the POITranslation model
            # this currently can't be handled by the FilterSortMixin
            query = search_form.cleaned_data.get("query")
            poi_keys = self.translation_model.search(
                region, language_slug, query
            ).values("poi__pk")
            qs = region.pois.filter(pk__in=poi_keys)
            pois = pois.union(qs)

        poi_chunk = self.paginate_queryset(pois)

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
                "is_archive": self.archived,
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
