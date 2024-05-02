def round_hix_score(raw_score: float | None) -> float | None:
    """
    Function to round HIX score
    """

    if raw_score is None:
        return None
    return round(raw_score, ndigits=2)
