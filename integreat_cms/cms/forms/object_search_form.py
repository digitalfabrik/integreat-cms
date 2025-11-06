from django import forms
from django.db.models import Q
from django.db.models.query import QuerySet


class ObjectSearchForm(forms.Form):
    """
    Form for searching objects
    """

    query = forms.CharField(min_length=1, required=False)

    search_fields: list[str] | None = None  # To be overridden in child classes

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        search_query = self.cleaned_data.get("query")
        if search_query:
            if self.search_fields is not None:
                queryset = queryset.filter(
                    Q(
                        *[
                            Q(**{f"{field}__icontains": search_query})
                            for field in self.search_fields
                        ],
                        _connector=Q.OR,
                    )
                )
            else:
                queryset = queryset.none()
        return queryset
