"""
Mixins for Django models in the CMS application.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, ClassVar, TYPE_CHECKING

from django.db import models
from django.db.models import Q, QuerySet

from ..search.matchers import TrigramMatcher
from ..search.scorer import score_token
from ..search.tokenizer import tokenize

if TYPE_CHECKING:
    from ..models.regions.region import Region

#: Minimum trigram similarity threshold for including a match
DEFAULT_MIN_SIMILARITY: float = 0.2

#: Maximum number of objects to process for suggestions
MAX_OBJECTS: int = 200

#: Minimum query length required to return suggestions
MIN_QUERY_LENGTH: int = 2


def normalize_search_fields(search_fields: dict) -> dict[str, dict[str, Any]]:
    """
    Normalize search_fields into a uniform structure with weight and tokenize keys.

    :param search_fields: Raw search field configuration from model
    :return: Normalized configuration with explicit weight and tokenize values
    """
    normalized: dict[str, dict[str, Any]] = {}

    for field, config in search_fields.items():
        if isinstance(config, int | float):
            normalized[field] = {
                "weight": float(config),
                "tokenize": True,
            }
        else:
            normalized[field] = {
                "weight": float(config.get("weight", 1.0)),
                "tokenize": bool(config.get("tokenize", True)),
            }

    return normalized


class SearchSuggestMixin(models.Model):
    """
    Mixin providing suggest_tokens() based on the model's search_fields attribute.

    Models using this mixin should define:
        - search_fields: dict mapping field names to weights or config dicts
        - region_filter_field: str | None - the field path for region filtering

    Example::

        class MyModel(AbstractBaseModel, SearchSuggestMixin):
            search_fields = {
                "title": 2.0,                    # Simple weight
                "name": {"weight": 1.5, "tokenize": True},  # Full config
                "email": {"weight": 1.0, "tokenize": False},  # Don't tokenize
            }
            region_filter_field = "region"

    A future addition could be to provide search() and suggest() methods
    that also use the search_fields attribute.
    Currently, search() and suggest() are defined on each model separately
    with different signatures.
    """

    #: Fields to search with their weights. Override in subclass.
    search_fields: ClassVar[dict[str, float | dict[str, Any]]] = {}

    #: Field path for region filtering (e.g., "region", "event__region"). None for global.
    region_filter_field: ClassVar[str | None] = None

    class Meta:
        abstract = True

    @classmethod
    def suggest_tokens(
        cls,
        query: str,
        region: Region | None = None,
        **kwargs: Any,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Generate search term suggestions using trigram similarity scoring.

        Filters objects using substring matching (icontains), then uses
        trigram similarity to score and rank the matching tokens.

        :param query: The search query string
        :param region: The region to filter by (optional)
        :param kwargs: Additional arguments (unused, for compatibility)
        :return: Dict with "suggestions" key containing list of {suggestion, score} dicts
        """
        query = query.strip()

        if not query or len(query) < MIN_QUERY_LENGTH:
            return {"suggestions": []}

        if not cls.search_fields:
            return {"suggestions": []}

        query = query.lower()
        fields = normalize_search_fields(cls.search_fields)

        matcher = TrigramMatcher()
        # Scores are accumulated per token - duplicate suggestions from multiple
        # fields or objects are automatically merged by summing their scores
        scores: defaultdict[str, float] = defaultdict(float)

        # Build filter for any field containing the query
        q_filter = Q()
        for field in fields:
            q_filter |= Q(**{f"{field}__icontains": query})

        qs: QuerySet[Any] = cls.objects.filter(q_filter)

        # Apply region filter if provided
        if region and cls.region_filter_field:
            qs = qs.filter(**{cls.region_filter_field: region})

        # Annotate with similarity scores for each field
        for field in fields:
            qs = matcher.annotate(qs, field, query)

        qs = qs[:MAX_OBJECTS]

        # Score tokens from matching objects
        for obj in qs:
            for field, config in fields.items():
                similarity: float = getattr(obj, matcher.sim_alias(field), 0.0) or 0.0
                if similarity < DEFAULT_MIN_SIMILARITY:
                    continue

                value: str = getattr(obj, matcher.value_alias(field), "") or ""
                if not value:
                    continue

                tokens = tokenize(value) if config["tokenize"] else {value}
                for token in tokens:
                    scores[token] += score_token(
                        similarity=similarity,
                        weight=config["weight"],
                        prefix_match=token.lower().startswith(query),
                    )

        return {
            "suggestions": [
                {"suggestion": token, "score": score} for token, score in scores.items()
            ]
        }
