"""
Helper function to clean TüNews HTML content.
"""

import re
from io import StringIO

from lxml import etree


def clean_html(html_string: str) -> str:
    """
    Remove unnecessary HTML elements.
    """
    root = etree.parse(StringIO("<main>" + html_string + "</main>"), etree.HTMLParser())
    xpath_pvc = '//*[contains(@class, "pvc_")]'

    for pvc in root.xpath(xpath_pvc):
        pvc.getparent().remove(pvc)
    main = root.xpath("body/main")[0]

    return etree.tostring(main, pretty_print=True).decode("utf-8")


def get_enewsno(html_string: str) -> str | int:
    """
    Get TüNews E-News-No from HTML string
    """
    enewsno = re.search("tun[0-9]{8}", html_string)
    if enewsno:
        return enewsno.group(0)
    return 0
