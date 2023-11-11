from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import unquote

from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from ..constants import region_status
from ..models import Region

if TYPE_CHECKING:
    from django.db.models.fields.related import RelatedManager
    from linkcheck.models import Url

    from ..models import Event, Language, Page, POI

logger = logging.getLogger(__name__)


def mark_valid(url: Url) -> None:
    """
    :param url: The internal URL to mark as valid
    """
    url.reset_for_check()
    url.status = True
    url.status_code = 200
    url.last_checked = timezone.now()
    url.save()


def mark_invalid(url: Url, error_message: str = "") -> None:
    """
    :param url: The internal URL to mark as invalid
    :param error_message: The reason why this URL is invalid
    """
    url.reset_for_check()
    url.status = False
    url.error_message = error_message
    url.last_checked = timezone.now()
    url.save()


def check_imprint(
    url: Url, path_components: list[str], region: Region, language: Language
) -> bool:
    """
    Check whether the imprint exists in the given region and language

    :param url: The internal URL to check
    :param path_components: The path components
    :param region: The region
    :param language: The language
    :returns: The validity status of the URL
    """
    if (
        len(path_components) == 1
        and region.imprint
        and region.imprint.get_public_translation(language.slug)
    ):
        mark_valid(url)
    else:
        logger.debug(
            "Imprint of %r in %r does not exist or is not public", region, language
        )
        mark_invalid(url, _("Imprint does not exist or is not public in this language"))
    return url.status


# pylint: disable=too-many-branches
def check_news_link(
    url: Url, path_components: list[str], region: Region, language: Language
) -> bool | None:
    """
    Check whether the news exists in the given region

    :param url: The internal URL to check
    :param path_components: The path components
    :param region: The region
    :param language: The language
    :returns: The validity status of the URL
    """
    if len(path_components) == 1:
        mark_invalid(
            url, _("News links require a subcategory (either 'local' or 'tu-news')")
        )
    elif len(path_components) <= 3:
        if path_components[1] == "tu-news":
            if region.external_news_enabled:
                if len(path_components) == 2:
                    logger.debug("Link to tü-news list in %r is valid", region)
                    mark_valid(url)
                else:
                    logger.debug(
                        "Skipping check of tü-news with id %r", path_components[2]
                    )
            else:
                logger.debug("tü-news are disabled in %r", region)
                mark_invalid(url, _("tü-news are disabled in this region."))
        elif path_components[1] == "local":
            if len(path_components) == 2:
                mark_valid(url)
            elif region.push_notifications.filter(
                id=path_components[2],
                sent_date__isnull=False,
                translations__language=language,
            ).exists():
                mark_valid(url)
            else:
                logger.debug(
                    "News with id %r does not exist in %r or was not sent in %r",
                    path_components[2],
                    language,
                    region,
                )
                mark_invalid(url, _("This news entry does not exist or was not sent."))
        else:
            logger.debug("News subcategory %r does not exist", path_components[1])
            mark_invalid(url, _("This news subcategory does not exist."))
    else:
        logger.debug(
            "News model is not hierarchical, got multiple path components %r",
            path_components,
        )
        mark_invalid(url, _("News URL is invalid."))
    return url.status


def check_offer_link(url: Url, path_components: list[str], region: Region) -> bool:
    """
    Check whether the offer exists in the given region

    :param url: The internal URL to check
    :param path_components: The path components
    :param region: The region
    :returns: The validity status of the URL
    """
    if not region.offers.exists():
        logger.debug("No offers are enabled in %r", region)
        mark_invalid(url, _("Offers are not enabled in this region."))
    elif len(path_components) == 1:
        logger.debug("Link to offer list in %r is valid", region)
        mark_valid(url)
    elif len(path_components) == 2:
        if region.offers.filter(slug=path_components[1]).exists():
            mark_valid(url)
        else:
            logger.debug(
                "Offer %r does not exist or is not enabled in %r",
                path_components[1],
                region,
            )
            mark_invalid(url, _("This offer does not exist in this region."))
    else:
        logger.debug(
            "Offer model is not hierarchical, got multiple path components %r",
            path_components,
        )
        mark_invalid(url, _("Offer URL is invalid"))
    return url.status


def check_translation_link(
    content_object: Event | (Page | POI), url: Url, language: Language
) -> bool:
    """
    Check whether the link of the given content object is valid

    :param content_object: The content object
    :param url: The internal URL to check
    :param language: The language
    """
    if content_object.archived:
        logger.debug("%r is archived", content_object)
        mark_invalid(url, _("The link target is archived."))
    elif translation := content_object.get_public_translation(language.slug):
        if translation.get_absolute_url().strip("/") != unquote(url.internal_url).strip(
            "/"
        ):
            logger.debug(
                "%r has different URL (%r) than the checked URL (%r)",
                translation,
                translation.get_absolute_url(),
                url.internal_url,
            )
            mark_invalid(url, _("The URL is not up-to-date."))
        else:
            mark_valid(url)
    else:
        logger.debug(
            "%r is not public in %r",
            content_object,
            language,
        )
        mark_invalid(url, _("The link target is not public in this language."))
    return url.status


def check_object_link(
    content_type: str,
    manager: RelatedManager,
    slug: str,
    url: Url,
    region: Region,
    language: Language,
) -> bool:
    """
    Check whether the given content objects are valid

    :param content_type: The content type (``Page``, ``Event`` or ``POI``)
    :param manager: The object manager
    :param url: The internal URL to check
    :param slug: The slug of the translation
    :param region: The region
    :param language: The language
    """
    objects = manager.filter(
        translations__slug=slugify(slug, allow_unicode=True),
        translations__language=language,
    ).distinct()
    if not objects and region.fallback_translations_enabled:
        objects = manager.filter(
            translations__slug=slugify(slug, allow_unicode=True),
            translations__language=region.default_language,
        ).distinct()
    if not objects:
        logger.debug(
            "%s with slug %r does not exist in %r and %r",
            content_type,
            slug,
            region,
            language,
        )
        mark_invalid(
            url, _("The link target does not exist in this region and language.")
        )
    elif len(objects) == 1:
        check_translation_link(objects[0], url, language)
    else:
        logger.warning(
            "%s slug %r is not unique in %r and %r (also returned %r)",
            content_type,
            slug,
            region,
            language,
            objects,
        )
        mark_invalid(
            url, _("The link target is not unique in this region and language.")
        )
    return url.status


def check_event_or_location(
    content_type: str,
    manager: RelatedManager,
    url: Url,
    path_components: list[str],
    region: Region,
    language: Language,
) -> bool:
    """
    Check whether the event or location with that URL exists in the given region and language.
    Fallback translations are also checked when they are enabled in the specific region.

    :param content_type: The content type (``Event`` or ``POI``)
    :param manager: The object manager
    :param url: The internal URL to check
    :param path_components: The path components
    :param region: The region
    :param language: The language
    :returns: The validity status of the URL
    """
    if len(path_components) == 1:
        logger.debug(
            "Link to %s list of %r in %r is valid", content_type, region, language
        )
        mark_valid(url)
    elif len(path_components) == 2:
        check_object_link(
            content_type,
            manager,
            path_components[1],
            url,
            region,
            language,
        )
    else:
        logger.debug(
            "%s model is not hierarchical, got multiple path components %r",
            content_type,
            path_components,
        )
        mark_invalid(url, _("This link is invalid."))
    return url.status


# pylint: disable=too-many-return-statements
def check_internal(url: Url) -> bool | None:
    """
    :param url: The internal URL to check
    :returns: The status of the URL
    """
    logger.debug(
        "Checking %r (type: %r, internal: %r)", url, url.type, url.internal_url
    )

    if url.type == "empty" or url.internal_url == "/":
        logger.debug("Marking empty link as valid")
        mark_valid(url)
        return url.status

    if url.type != "internal":
        logger.debug("Skipping type %r", url.type)
        return url.status

    prepared_url = unquote(url.internal_url).strip("/")
    if "/" not in prepared_url:
        prepared_url += "/"
    region_slug, language_and_path = prepared_url.split("/", maxsplit=1)
    region = (
        Region.objects.filter(slug=region_slug)
        .exclude(status=region_status.ARCHIVED)
        .first()
    )
    if not region:
        logger.debug("Region with slug %r does not exist or is not active", region_slug)
        mark_invalid(url, _("This region does not exist or is not active."))
        return url.status

    if not language_and_path:
        logger.debug(
            "Link to category overview of %r in the default language is valid", region
        )
        mark_valid(url)
        return url.status

    if "/" not in language_and_path:
        language_and_path += "/"
    language_slug, path = language_and_path.split("/", maxsplit=1)
    try:
        language = region.get_language_or_404(
            language_slug, only_active=True, only_visible=True
        )
    except Http404:
        logger.debug(
            "Language with slug %r does not exist or is not active & visible",
            language_slug,
        )
        mark_invalid(
            url, _("This language does not exist or is not active and visible.")
        )
        return url.status

    if not path:
        logger.debug("Link to category overview of %r in %r is valid", region, language)
        mark_valid(url)
        return url.status

    path_components = path.split("/")
    content_type = path_components[0]
    if content_type == settings.IMPRINT_SLUG:
        return check_imprint(url, path_components, region, language)
    if content_type == "events":
        return check_event_or_location(
            "Event", region.events, url, path_components, region, language
        )
    if content_type == "locations":
        return check_event_or_location(
            "POI", region.pois, url, path_components, region, language
        )
    if content_type == "news":
        return check_news_link(url, path_components, region, language)
    if content_type == "offers":
        return check_offer_link(url, path_components, region)
    return check_object_link(
        "Page", region.pages, path_components[-1], url, region, language
    )
