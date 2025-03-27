from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from integreat_cms.cms.models import PageTranslation, Region

from integreat_cms.cms.views.utils.hix import get_translation_under_hix_threshold

register = template.Library()


@register.simple_tag
def get_translations_under_hix_threshold(region: Region) -> QuerySet[PageTranslation]:
    return get_translation_under_hix_threshold(region)
