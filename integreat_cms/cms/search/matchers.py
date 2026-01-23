from abc import ABC, abstractmethod

from django.contrib.postgres.search import TrigramSimilarity


class BaseMatcher(ABC):
    @abstractmethod
    def annotate(self, queryset, field: str, query: str):
        """
        Return queryset annotated with a similarity score for `field`.
        """


class TrigramMatcher(BaseMatcher):
    def annotate(self, queryset, field: str, query: str):
        return queryset.annotate(**{f"{field}_sim": TrigramSimilarity(field, query)})
