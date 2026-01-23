def score_token(
    *,
    similarity: float,
    weight: float,
) -> float:
    """
    Compute the score contribution of a single token.
    """
    return similarity * weight
