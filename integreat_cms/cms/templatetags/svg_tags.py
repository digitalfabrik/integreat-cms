"""
Contains a collection of tags for working with svg icons.
"""

from __future__ import annotations

from django import template

from ..utils.tinymce_icon_utils import get_icon_url

register = template.Library()


@register.simple_tag
def get_svg_icon(svg: str) -> str:
    """
    This tags inserts the link to an svg icon

    :param svg: The svg icon to insert

    :return: The full url of the svg
    """
    return get_icon_url(svg)
