from django.db.models import QuerySet

from ...forms import ObjectSearchForm
from ...search.search_fields import CONTACT_SEARCH_FIELDS


class ContactSearchForm(ObjectSearchForm):
    search_fields = CONTACT_SEARCH_FIELDS

    def apply_filters(self, queryset: QuerySet) -> QuerySet:
        return super().apply_filters(queryset).distinct()
