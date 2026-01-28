from abc import ABC, abstractmethod

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F


class BaseMatcher(ABC):
    @abstractmethod
    def annotate(self, queryset, field: str, query: str):
        """
        Return queryset annotated with a similarity score for `field`.
        """

    def value_alias(self, field: str) -> str:
        return f"{field.replace('__', '_')}_value"

    def sim_alias(self, field: str) -> str:
        return f"{field.replace('__', '_')}_sim"


class TrigramMatcher(BaseMatcher):
    def annotate(self, queryset, field: str, query: str):
        return queryset.annotate(
            **{
                self.value_alias(field): F(field),
                self.sim_alias(field): TrigramSimilarity(field, query),
            }
        )
