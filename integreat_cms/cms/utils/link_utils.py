from __future__ import annotations

import re
from urllib.parse import ParseResult, unquote, urlparse

from django.conf import settings


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


def format_phone_number(phone_number: str) -> str:
    """
    Format given phone number

    :param phone_number: The phone number to format
    :return: The formatted phone number
    """
    if not phone_number or re.fullmatch(r"^\+\d{2,3} \(0\) \d*$", phone_number):
        return phone_number

    phone_number = re.sub(r"[^0-9+]", "", phone_number)
    prefix = settings.DEFAULT_PHONE_NUMBER_COUNTRY_CODE
    if phone_number.startswith("00"):
        prefix = f"+{phone_number[2:4]}"
        phone_number = phone_number[4:]
    elif phone_number.startswith("0"):
        phone_number = phone_number[1:]
    elif phone_number.startswith("+"):
        prefix = phone_number[0:3]
        phone_number = phone_number[3:]

    return f"{prefix} (0) {phone_number}"
