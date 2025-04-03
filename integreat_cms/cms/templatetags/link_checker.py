"""
Template tag for the link checker column in region condition
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from integreat_cms.cms.models import Region

from integreat_cms.cms.utils.linkcheck_utils import filter_urls

register = template.Library()


@register.simple_tag
def get_broken_links(region: Region) -> int:
    _, count_dict = filter_urls(region_slug=region.slug)
    return count_dict["number_invalid_urls"]
