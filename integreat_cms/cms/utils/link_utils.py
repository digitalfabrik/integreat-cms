from __future__ import annotations

import re
from urllib.parse import ParseResult, unquote, urlparse


def fix_domain_encoding(url: re.Match[str]) -> str:
    """
    Fix the encoding of punycode domains

    :param url: The input url match
    :return: The fixed url
    """
    parsed_url: ParseResult = urlparse(url.group(1))
    parsed_url = parsed_url._replace(netloc=unquote(parsed_url.netloc))
    return parsed_url.geturl()


def fix_content_link_encoding(content: str) -> str:
    """
    Fix the encoding of punycode domains in an html content string

    :param content: The input content
    :return: The fixed content
    """
    return re.sub(r"(?<=[\"'])(https?://.+?)(?=[\"'])", fix_domain_encoding, content)
