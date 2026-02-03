from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F

if TYPE_CHECKING:
    from django.db.models import QuerySet


class BaseMatcher(ABC):
    """Base class for search matchers that annotate querysets with similarity scores."""

    @abstractmethod
    def annotate(self, queryset: QuerySet, field: str, query: str) -> QuerySet:
        """
        Annotate queryset with similarity score for a field.

        :param queryset: The queryset to annotate
        :param field: The field name to compute similarity for
        :param query: The search query to match against
        :return: Annotated queryset with value and similarity aliases
        """

    def value_alias(self, field: str) -> str:
        """Get the alias name for the field value annotation."""
        return f"{field.replace('__', '_')}_value"

    def sim_alias(self, field: str) -> str:
        """Get the alias name for the similarity score annotation."""
        return f"{field.replace('__', '_')}_sim"


class TrigramMatcher(BaseMatcher):
    """Matcher using PostgreSQL trigram similarity for fuzzy matching."""

    def annotate(self, queryset: QuerySet, field: str, query: str) -> QuerySet:
        """
        Annotate queryset with trigram similarity score.

        :param queryset: The queryset to annotate
        :param field: The field name to compute similarity for
        :param query: The search query to match against
        :return: Queryset annotated with field value and similarity score
        """
        return queryset.annotate(
            **{
                self.value_alias(field): F(field),
                self.sim_alias(field): TrigramSimilarity(field, query),
            }
        )
