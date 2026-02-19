from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models import Language
from ..mixins import FilterSortMixin, PaginationMixin

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_language"), name="dispatch")
class LanguageListView(TemplateView, FilterSortMixin, PaginationMixin):
    """
    View for listing languages
    """

    #: Template for list of non-archived languages
    template_name = "languages/language_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "languages"}
    model = Language

    def get_filtered_sorted_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Also match languages by their translated name, which is a Python property
        and cannot be filtered in SQL.

        :param queryset: The queryset of languages
        :return: The filtered and sorted queryset
        """
        form = self.get_filter_form()
        if form and form.is_valid():
            query = form.cleaned_data.get("search_query")
            if query:
                translated_name_pks = [
                    lang.pk
                    for lang in Language.objects.all()
                    if query.lower() in lang.translated_name.lower()
                ]
                queryset = form.apply_filters(queryset) | Language.objects.filter(
                    pk__in=translated_name_pks
                )
        order_by = [
            f
            for f in self.request.GET.getlist("sort")
            if f.lstrip("-") in self.sort_fields
        ]
        if order_by:
            return queryset.order_by(*order_by)
        return queryset

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render language list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        languages = Language.objects.all()
        search_query = request.GET.get("search_query") or None

        languages = self.get_filtered_sorted_queryset(languages)
        language_chunk = self.paginate_queryset(languages)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "languages": language_chunk,
                "search_query": search_query,
            },
        )
