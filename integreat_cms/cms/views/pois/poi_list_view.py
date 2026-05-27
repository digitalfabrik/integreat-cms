from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.db.models import Case, IntegerField, OuterRef, Subquery, Value, When
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import permission_required
from ...models import POI, POICategoryTranslation, POITranslation
from ..mixins import FilterSortMixin, MachineTranslationContextMixin, PaginationMixin
from .poi_context_mixin import POIContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet
    from django.http import HttpRequest, HttpResponse


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
    model = POI
    table_fields = [
        ("_sort_title", _("Title")),
        ("_sort_status", _("Publication status")),
        ("address", _("Street")),
        ("postcode", _("Postal Code")),
        ("city", _("City")),
        ("country", _("Country")),
        ("_sort_category_name", _("Category")),
    ]

    def get_filtered_sorted_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Annotate sort keys that match what the user actually sees in the list:

        * ``_sort_title`` and ``_sort_status``: latest translation (any version,
          including auto-saves) in the language slug from the URL — this is the
          translation rendered by ``poi_list_row.html``.
        * ``_sort_status`` ranks status values by workflow order (AUTO_SAVE, DRAFT,
          REVIEW, PUBLIC) instead of by the lexicographic order of
          the choice keys, which has no relation to the localized labels shown.
        * ``_sort_category_name``: name of the category in the active backend
          (UI) language, mirroring how :class:`POICategory.__str__` renders the
          column.
        """
        latest_translation = POITranslation.objects.filter(
            poi=OuterRef("pk"),
            language__slug=self.kwargs["language_slug"],
        ).order_by("-version")
        ranked_status = latest_translation.annotate(
            _rank=Case(
                When(status=status.AUTO_SAVE, then=Value(0)),
                When(status=status.DRAFT, then=Value(1)),
                When(status=status.REVIEW, then=Value(2)),
                When(status=status.PUBLIC, then=Value(3)),
                output_field=IntegerField(),
            ),
        )
        category_translation = POICategoryTranslation.objects.filter(
            category=OuterRef("category_id"),
            language__slug=get_language(),
        )
        queryset = queryset.annotate(
            _sort_title=Subquery(latest_translation.values("title")[:1]),
            _sort_status=Subquery(ranked_status.values("_rank")[:1]),
            _sort_category_name=Subquery(category_translation.values("name")[:1]),
        )
        return super().get_filtered_sorted_queryset(queryset)

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
        search_query = request.GET.get("search_query") or None

        pois = self.get_filtered_sorted_queryset(pois)
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
                "search_query": search_query,
                "source_language": region.get_source_language(language.slug),
                "content_type": "locations",
                "is_archive": self.archived,
                "title_label": "{} {}".format(_("Title in"), language.translated_name),
            },
        )
