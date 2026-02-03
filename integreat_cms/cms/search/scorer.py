from __future__ import annotations


def score_token(
    *,
    similarity: float,
    weight: float,
) -> float:
    """
    Compute the score contribution of a single token.

    :param similarity: The trigram similarity score (0.0 to 1.0)
    :param weight: The field weight multiplier
    :return: The weighted score for this token
    """
    return similarity * weight
