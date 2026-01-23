from django.db import models


class SearchSuggestMixin(models.Model):
    """
    Mixin to provide search suggestions for objects
    """

    search_fields = {}

    class Meta:
        abstract = True

    @classmethod
    def suggest(cls, query):
        pass

    def validate_search_field(self, field):
        pass
