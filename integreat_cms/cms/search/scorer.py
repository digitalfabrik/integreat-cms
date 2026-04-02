from __future__ import annotations

#: Boost multiplier for tokens that start with the query
PREFIX_BOOST: float = 1.5


def score_token(
    *,
    similarity: float,
    weight: float,
    prefix_match: bool = False,
) -> float:
    """
    Compute the score contribution of a single token.

    :param similarity: The trigram similarity score (0.0 to 1.0)
    :param weight: The field weight multiplier
    :param prefix_match: Whether the token starts with the query
    :return: The weighted score for this token
    """
    score = similarity * weight
    if prefix_match:
        score *= PREFIX_BOOST
    return score
