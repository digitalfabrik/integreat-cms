from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from integreat_cms.cms.models import Region


register = template.Library()


@register.simple_tag
def get_partially_translated_pages(region: Region) -> int:
    return region.get_partially_translated_pages()
