import re

TOKEN_RE = re.compile(r"\w+")


def tokenize(value: str) -> set[str]:
    """
    Convert a string into normalized search tokens.
    """
    if not value:
        return set()

    return {t for t in TOKEN_RE.findall(value)}
