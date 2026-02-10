from __future__ import annotations

import re
from typing import Final

#: Pattern to extract word tokens from text
TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"\w+")


def tokenize(value: str) -> set[str]:
    """
    Convert a string into normalized search tokens.

    Extracts all word characters (alphanumeric and underscore) as individual tokens.

    :param value: The string to tokenize
    :return: Set of unique tokens found in the string
    """
    if not value:
        return set()

    return set(TOKEN_RE.findall(value))
