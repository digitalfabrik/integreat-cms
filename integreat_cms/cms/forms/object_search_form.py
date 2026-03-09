from __future__ import annotations

from typing import Any, TYPE_CHECKING

from django import forms
from django.db.models import Q

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class ObjectSearchForm(forms.Form):
    """
    Form for searching objects
    """

    search_query = forms.CharField(min_length=1, required=False)

    search_fields: list[str]

    def __init__(self, *args: Any, search_fields: list[str], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not search_fields:
            raise ValueError("no search_fields provided for ObjectSearchForm")
        self.search_fields = search_fields

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        search_query = self.cleaned_data.get("search_query")
        if search_query:
            queryset = queryset.filter(
                Q(
                    *[
                        Q(**{f"{field}__icontains": search_query})
                        for field in self.search_fields
                    ],
                    _connector=Q.OR,
                )
            )
            if any("__" in field for field in self.search_fields):
                queryset = queryset.distinct()
        return queryset
