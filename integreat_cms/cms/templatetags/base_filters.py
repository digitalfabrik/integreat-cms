from __future__ import annotations

from typing import TYPE_CHECKING

from django import template
from django.conf import settings

if TYPE_CHECKING:
    from django.contrib.auth.context_processors import PermWrapper
    from django.utils.safestring import SafeString

    from ..models.regions.region import Region

register = template.Library()


@register.filter
def in_list(value: str | None, comma_separated_list: SafeString) -> bool:
    """
    This filter checks whether a given string value is contained in a comma separated list

    :param value: The value which should be checked
    :param comma_separated_list: The list of comma-separated strings
    :return: Whether or not value is contained in the list
    """
    return value in comma_separated_list.split(",")


@register.simple_tag
def get_mt_visibility(region: Region, perms: PermWrapper) -> bool:
    """
    This tag checks whether either DeepL or Google Translate or SUMM.AI is activated in the region and the user has permission to manage automatic translations.

    :param region: The rcurrent region
    :param perms: Permission of the user
    :return: Whether the MT section should be shown
    """
    return "cms.manage_translations" in perms and (
        settings.DEEPL_ENABLED
        or settings.GOOGLE_TRANSLATE_ENABLED
        or (settings.SUMM_AI_ENABLED and region.summ_ai_enabled)
    )
