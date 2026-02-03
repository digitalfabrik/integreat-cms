from __future__ import annotations

from collections import defaultdict
from typing import Any, TYPE_CHECKING

from django.db.models import Q

from .matchers import TrigramMatcher
from .scorer import score_token
from .tokenizer import tokenize

if TYPE_CHECKING:
    from django.db.models import Model

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


def suggest_tokens_for_model(
    model_cls: type[Model],
    query: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Generate search term suggestions for a model based on a query.

    Filters objects using substring matching (icontains), then uses
    trigram similarity to score and rank the matching tokens.

    :param model_cls: The Django model class to search
    :param query: The search query string
    :return: Dict with "suggestions" key containing list of {suggestion, score} dicts
    """
    query = query.strip()

    if not query or len(query) < MIN_QUERY_LENGTH:
        return {"suggestions": []}

    query = query.lower()
    fields = normalize_search_fields(model_cls.search_fields)

    matcher = TrigramMatcher()
    # Scores are accumulated per token - duplicate suggestions from multiple
    # fields or objects are automatically merged by summing their scores
    scores: defaultdict[str, float] = defaultdict(float)

    # Build filter for any field containing the query
    q_filter = Q()
    for field in fields:
        q_filter |= Q(**{f"{field}__icontains": query})

    qs: Any = model_cls.objects.filter(q_filter)

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
