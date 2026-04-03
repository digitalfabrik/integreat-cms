"""
This file contains utility functions for content translations.
"""

from __future__ import annotations

import logging
import operator
from functools import reduce
from typing import Any, TYPE_CHECKING

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from linkcheck.models import Url

from .content_utils import clean_content
from .internal_link_utils import get_public_translation_for_link

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..models import User
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)

MAX_RETRY = 3  # number of retry attempts when hitting the translation version number race condition


def save_new_version_with_retry(
    translation: AbstractContentTranslation,
    save_fn: Callable[[], Any],
) -> Any:
    """
    Call *save_fn* inside a savepoint, retrying with a recomputed version
    number when a :class:`~django.db.IntegrityError` on the
    ``unique_version`` constraint is raised (up to 3 attempts).

    This handles race conditions where concurrent requests both try to
    insert a new version with the same ``(foreign_object, language, version)``
    tuple.

    :param translation: The content translation whose ``version`` field will
        be corrected on conflict
    :param save_fn: A zero-argument callable that persists *translation*
        (e.g. ``lambda: form.save(commit=True)`` or ``translation.save``)
    :return: Whatever *save_fn* returns
    """
    foreign_field = translation.foreign_field()
    foreign_id = getattr(translation, f"{foreign_field}_id")

    for attempt in range(MAX_RETRY):
        try:
            with transaction.atomic():
                return save_fn()
        except IntegrityError as e:
            if "unique_version" not in str(e) or attempt >= 2:
                raise
            # Recompute the next version from the database
            max_version = (
                (
                    type(translation)
                    .objects.filter(
                        **{foreign_field: foreign_id, "language": translation.language}
                    )
                    .aggregate(max_v=Max("version"))["max_v"]
                )
                or 0
            )
            translation.version = max_version + 1
            logger.info(
                "Version conflict on %r, retrying with version %d",
                translation,
                translation.version,
            )
    return None  # unreachable, but satisfies type checkers


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
