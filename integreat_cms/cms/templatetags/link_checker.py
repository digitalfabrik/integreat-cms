"""
Template tag for the link checker column in region condition
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template
from django.utils.translation import get_language

if TYPE_CHECKING:
    from typing import Any

    from linkcheck.models import Link

    from integreat_cms.cms.models import Region

from integreat_cms.cms.models.abstract_content_translation import (
    AbstractContentTranslation,
)
from integreat_cms.cms.utils.linkcheck_utils import filter_urls

register = template.Library()


@register.simple_tag
def get_broken_links(region: Region) -> int:
    _, count_dict = filter_urls(region_slug=region.slug)
    return count_dict["number_invalid_urls"]


@register.simple_tag
def link_display_info(links: list[Link], region: Region | None) -> dict[str, Any]:
    # Fall back to user language if user is in the global link list or the region's `default_language` returns `None`
    preferred_language_slug = (
        region.default_language.slug
        if region and region.default_language
        else get_language()
    )

    first_content, link_text = links[0].content_object, links[0].text
    best_content, link_text = next(
        (
            (link.content_object, link.text)
            for link in links
            if isinstance(link.content_object, AbstractContentTranslation)
            and link.content_object.language.slug == preferred_language_slug
        ),
        (first_content, link_text),
    )

    best_content_translation = (
        best_content.foreign_object.get_translation(preferred_language_slug)
        if isinstance(best_content, AbstractContentTranslation)
        else None
    )

    title_in_readable_language = (
        best_content_translation.title
        if best_content_translation
        and best_content.language.slug != preferred_language_slug
        else None
    )

    link = (
        f"{best_content.base_link}{best_content.slug}"
        if isinstance(best_content, AbstractContentTranslation)
        else best_content.backend_edit_link
    )

    return {
        "title": best_content.title,
        "link": link,
        "text": link_text,
        "translated_title": title_in_readable_language,
    }
