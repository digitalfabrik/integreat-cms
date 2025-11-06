from django.db.models import QuerySet

from ...forms import ObjectSearchForm


class ContactSearchForm(ObjectSearchForm):
    search_fields = ["name", "location__translations__title", "area_of_responsibility"]

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        return super().apply_filters(queryset).distinct()
