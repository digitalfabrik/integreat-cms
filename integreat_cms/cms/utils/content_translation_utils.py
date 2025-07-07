"""
This file contains utility functions for content translations.
"""

from __future__ import annotations

import logging
import operator
from functools import reduce
from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Q
from linkcheck.models import Url

from .content_utils import clean_content
from .internal_link_utils import get_public_translation_for_link

if TYPE_CHECKING:
    from ..models import User
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def update_links_to(
    content_translation: AbstractContentTranslation,
    user: User | None,
) -> None:
    """
    Updates all content translations with links that point to the given translation.
    This fixes potentially outdated links.

    :param content_translation: The content translation for which links that points to it should get updated
    :param user: The user who should be responsible for updating the links
    """
    for outdated_content_translation in get_referencing_translations(
        content_translation,
    ):
        # Assert that the related translation is not archived
        # Note that this should not be possible, since links to archived pages get deleted
        if getattr(outdated_content_translation.foreign_object, "archived", False):
            continue

        new_content = clean_content(
            outdated_content_translation.content,
            outdated_content_translation.language.slug,
        )
        if new_content == outdated_content_translation.content:
            continue

        fixed_content_translation = (
            outdated_content_translation.create_new_version_copy(user)
        )
        fixed_content_translation.content = new_content
        outdated_content_translation.links.all().delete()
        fixed_content_translation.save()

        logger.debug(
            "Updated links to %s in %r",
            content_translation.full_url,
            outdated_content_translation,
        )


def get_referencing_translations(
    content_translation: AbstractContentTranslation,
) -> set[AbstractContentTranslation]:
    """
    Returns a list of content translations that link to the given translation

    :param content_translation: The `content_translation` for which links should be searched
    :return: All referencing content translations
    """
    result: set[AbstractContentTranslation] = set()

    public_translation = content_translation.public_version

    # To avoid searching every single url, filter for urls that contain a slug or id that the content translation has used
    translation_slugs = set(content_translation.get_all_used_slugs())
    translation_ids = set(content_translation.all_versions.values_list("id", flat=True))
    logger.debug(
        "Collecting links that contain %s or %s",
        translation_slugs,
        translation_ids,
    )
    # Links end in the slug or id, and might or might not have a trailing slash
    filter_query = reduce(
        operator.or_,
        (
            Q(url__endswith=f"/{slug}{trailing}")
            for slug in translation_slugs
            for trailing in ["", "/"]
        ),
    )
    filter_query = filter_query | reduce(
        operator.or_,
        (
            Q(url__endswith=f"/{uid}{trailing}")
            for uid in translation_ids
            for trailing in ["", "/"]
        ),
    )
    # Links also start with the domain followed by the region and language slug
    region_slug = content_translation.foreign_object.region.slug
    language_slug = content_translation.language.slug
    filter_query = filter_query & Q(
        url__startswith=f"{settings.WEBAPP_URL.removesuffix('/')}/{region_slug}/{language_slug}/"
    )

    urls = Url.objects.filter(filter_query)
    for url in urls:
        if linked_translation := get_public_translation_for_link(url.url):
            if linked_translation != public_translation:
                continue

            result.update(
                link.content_object.latest_version for link in url.links.all()
            )
    return result
