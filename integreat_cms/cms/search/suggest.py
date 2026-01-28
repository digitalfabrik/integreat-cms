from collections import defaultdict

from django.db.models import Q

from .matchers import TrigramMatcher
from .scorer import score_token
from .tokenize import tokenize

DEFAULT_MIN_SIMILARITY = 0.2
MAX_OBJECTS = 200
MAX_RESULTS = 10


def normalize_search_fields(search_fields: dict) -> dict[str, dict]:
    """
    Normalize search_fields into a uniform structure:
    {
        field_name: {
            "weight": float,
            "tokenize": bool,
        }
    }
    """
    normalized = {}

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


def suggest_tokens_for_model(model_cls, query: str) -> dict[str, list[dict]]:
    if not query:
        return {}

    query = query.lower().strip()
    fields = normalize_search_fields(model_cls.search_fields)

    matcher = TrigramMatcher()
    scores = defaultdict(float)

    q_filter = Q()
    for field in fields:
        q_filter |= Q(**{f"{field}__icontains": query})

    qs = model_cls.objects.filter(q_filter)

    for field in fields:
        qs = matcher.annotate(qs, field, query)

    qs = qs[:MAX_OBJECTS]

    for obj in qs:
        for field, config in fields.items():
            similarity = getattr(obj, matcher.sim_alias(field), 0.0)
            if similarity < DEFAULT_MIN_SIMILARITY:
                continue

            value = getattr(obj, matcher.value_alias(field), "") or ""
            if not value:
                continue

            tokens = tokenize(value) if config.get("tokenize", True) else {value}
            for token in tokens:
                scores[token] += score_token(
                    similarity=similarity,
                    weight=config.get("weight", 1.0),
                )

    return {
        "suggestions": [
            {"suggestion": token, "score": score} for token, score in scores.items()
        ]
    }
