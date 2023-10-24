"""
This file contains utilities related to icons in the tinymce editor
"""
from __future__ import annotations

from django.conf import settings
from django.templatetags.static import static
from lxml.html import Element


def get_icon_url(icon_name: str) -> str:
    """
    Returns the url to the given icon svg

    :param icon_name: The name of the icon
    :return: the url path to the asset
    """
    return settings.BASE_URL + static(f"svg/{icon_name}.svg")


def get_icon_html(icon_name: str) -> Element:
    """
    Returns the html for the given icon

    :param icon_name: The name of the icon
    :return: The html
    """
    img = Element("img")
    img.set("src", get_icon_url(icon_name))
    img.set("style", "width:15px; height:15px;")
    return img
