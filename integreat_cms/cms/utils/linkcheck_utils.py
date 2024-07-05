from __future__ import annotations

import logging
import re
import time
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, unquote, urlparse

from django.conf import settings
from django.db.models import Prefetch, Q, QuerySet, Subquery
from linkcheck import update_lock
from linkcheck.listeners import tasks_queue
from linkcheck.models import Link, Url
from lxml.html import rewrite_links

from integreat_cms.cms.models import (
    EventTranslation,
    ImprintPageTranslation,
    PageTranslation,
    POITranslation,
    Region,
)

from ..models.abstract_content_translation import AbstractContentTranslation

if TYPE_CHECKING:
    from typing import Any

    from ..models import Region, User

logger = logging.getLogger(__name__)


def get_urls(
    region_slug: str | None = None,
    url_ids: Any | None = None,
) -> list[Url] | QuerySet[Url]:
    """
    Collect all the urls which appear in the latest versions of the contents of the region, filtered by ID or region if given.

    :param region_slug: The slug of the current region
    :param url_ids: The list of requested url ids
    :return: The list (or queryset) of urls
    """
    urls = Url.objects.all()
    if url_ids is not None:
        # If the results should be limited to specific ids, filter the queryset
        urls = urls.filter(id__in=url_ids)
    if region_slug:
        region = Region.objects.get(slug=region_slug)
        region_links = get_region_links(region)

        # Prefetch all link objects of the requested region
        urls = (
            urls.filter(links__in=region_links)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "links",
                    queryset=region_links,
                    to_attr="region_links",
                )
            )
        )

    # Filter out ignored URL types
    if settings.LINKCHECK_IGNORED_URL_TYPES:
        return [
            url for url in urls if url.type not in settings.LINKCHECK_IGNORED_URL_TYPES
        ]

    return urls


def get_region_links(region: Region) -> QuerySet:
    """
    Returns the links of translations of the given region
    :param region: The region
    :return: A query containing the relevant links
    """
    latest_pagetranslation_versions = Subquery(
        PageTranslation.objects.filter(
            page__id__in=Subquery(region.non_archived_pages.values("pk")),
        )
        .distinct("page__id", "language__id")
        .values_list("pk", flat=True)
    )
    latest_poitranslation_versions = Subquery(
        POITranslation.objects.filter(poi__region=region)
        .distinct("poi__id", "language__id")
        .values_list("pk", flat=True)
    )
    latest_eventtranslation_versions = Subquery(
        EventTranslation.objects.filter(event__region=region)
        .distinct("event__id", "language__id")
        .values_list("pk", flat=True)
    )
    latest_imprinttranslation_versions = Subquery(
        ImprintPageTranslation.objects.filter(page__region=region)
        .distinct("page__id", "language__id")
        .values_list("pk", flat=True)
    )
    # Get all link objects of the requested region
    region_links = Link.objects.filter(
        Q(page_translation__id__in=latest_pagetranslation_versions)
        | Q(imprint_translation__id__in=latest_imprinttranslation_versions)
        | Q(event_translation__id__in=latest_eventtranslation_versions)
        | Q(poi_translation__id__in=latest_poitranslation_versions)
    ).order_by("id")

    return region_links


def get_url_count(region_slug: str | None = None) -> dict[str, int]:
    """
    Count all urls by status. The content objects are not prefetched because they are not needed for the counter.

    :param region_slug: The slug of the current region
    :return: A dictionary containing the counters of all remaining urls
    """
    _, count_dict = filter_urls(region_slug=region_slug)
    return count_dict


# pylint: disable=too-many-branches
def filter_urls(
    region_slug: str | None = None,
    url_filter: str | None = None,
) -> tuple[list[Url], dict[str, int]]:
    """
    Filter all urls of one region by the given category

    :param region_slug: The slug of the current region
    :param url_filter: Which urls should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all urls are returned by default.
    :return: A tuple of the requested urls and a dict containing the counters of all remaining urls
    """
    urls = get_urls(region_slug=region_slug)
    # Split url lists into their respective categories
    ignored_urls, valid_urls, invalid_urls, email_links, phone_links, unchecked_urls = (
        [] for _ in range(6)
    )
    for url in urls:
        links = url.region_links if region_slug else url.links.all()
        if all(link.ignore for link in links):
            ignored_urls.append(url)
        elif url.status:
            valid_urls.append(url)
        elif url.status is False:
            # Explicitly check for False, because status is None means unchecked
            invalid_urls.append(url)
        elif url.type == "mailto":
            email_links.append(url)
        elif url.type == "phone":
            phone_links.append(url)
        elif not url.last_checked:
            unchecked_urls.append(url)
        else:
            raise NotImplementedError(
                f"Url {url!r} does not fit into any of the defined categories"
            )
    # Pass the number of urls to a dict which can be used as extra template context
    count_dict = {
        "number_all_urls": len(urls),
        "number_valid_urls": len(valid_urls),
        "number_unchecked_urls": len(unchecked_urls),
        "number_ignored_urls": len(ignored_urls),
        "number_invalid_urls": len(invalid_urls),
    }
    if settings.LINKCHECK_EMAIL_ENABLED:
        count_dict["number_email_urls"] = len(email_links)
    if settings.LINKCHECK_PHONE_ENABLED:
        count_dict["number_phone_urls"] = len(phone_links)
    # Return the requested urls
    if url_filter == "valid":
        urls = valid_urls
    elif url_filter == "unchecked":
        urls = unchecked_urls
    elif url_filter == "ignored":
        urls = ignored_urls
    elif url_filter == "invalid":
        urls = invalid_urls
    elif url_filter == "email":
        urls = email_links
    elif url_filter == "phone":
        urls = phone_links

    return urls, count_dict


def replace_link_helper(old_url: str, new_url: str, link: str) -> str:
    """
    A small helper function which can be passed to :meth:`lxml.html.HtmlMixin.rewrite_links`

    :param old_url: The url which should be replaced
    :param new_url: The url which should be inserted instead of the old url
    :param link: The current link
    :return: The replaced link
    """
    return new_url if link == old_url else link


def save_new_version(
    translation: AbstractContentTranslation,
    new_translation: AbstractContentTranslation,
    user: Any | None,
) -> None:
    """
    Save a new translation version

    :param translation: The old translation
    :param new_translation: The new translation
    :param user: The creator of the new version
    """
    translation.links.all().delete()
    new_translation.pk = None
    new_translation.version += 1
    new_translation.minor_edit = True
    new_translation.creator = user
    new_translation.save()
    logger.debug("Created new translation version %r", new_translation)


# pylint: disable=too-many-locals
def replace_links(
    search: str,
    replace: str,
    *,
    region: Region | None = None,
    user: User | None = None,
    commit: bool = True,
    link_types: list[str] | None = None,
) -> None:
    """
    Perform search & replace in the content links

    :param search: The (partial) URL to search
    :param replace: The (partial) URL to replace
    :param region: Optionally limit the replacement to one region (``None`` means a global replacement)
    :param user: The creator of the replaced translations
    :param commit: Whether changes should be written to the database
    :param link_types: Which kind of links should be replaced
    """
    region_msg = f' of "{region!r}"' if region else ""
    user_msg = f' by "{user!r}"' if user else ""
    logger.info(
        "Replacing %r with %r in content links%s%s",
        search,
        replace,
        region_msg,
        user_msg,
    )
    models = [PageTranslation, EventTranslation, POITranslation]
    with update_lock:
        for model in models:
            filters = {}
            if region:
                filters[f"{model.foreign_field()}__region"] = region

            for translation in model.objects.filter(**filters).distinct(
                model.foreign_field(), "language"
            ):
                new_translation = deepcopy(translation)
                for link in translation.links.select_related("url"):
                    url = link.url.url
                    should_replace = search in url and (
                        not link_types or link.url.type in link_types
                    )
                    if should_replace:
                        fixed_url = url.replace(search, replace)
                        new_translation.content = rewrite_links(
                            new_translation.content,
                            partial(replace_link_helper, url, fixed_url),
                        )
                        logger.debug(
                            "Replacing %r with %r in %r", url, fixed_url, translation
                        )
                new_translation.content = fix_content_link_encoding(
                    new_translation.content
                )
                if new_translation.content != translation.content and commit:
                    save_new_version(translation, new_translation, user)
    # Wait until all post-save signals have been processed
    logger.debug("Waiting for linkcheck listeners to update link database...")
    time.sleep(0.1)
    tasks_queue.join()
    logger.info("Finished replacing %r with %r in content links", search, replace)


def fix_domain_encoding(url: re.Match[str]) -> str:
    """
    Fix the encoding of punycode domains

    :param url: The input url match
    :return: The fixed url
    """
    parsed_url: ParseResult = urlparse(url.group(1))
    parsed_url = parsed_url._replace(netloc=unquote(parsed_url.netloc))
    return parsed_url.geturl()


def fix_content_link_encoding(content: str) -> str:
    """
    Fix the encoding of punycode domains in an html content string

    :param content: The input content
    :return: The fixed content
    """
    return re.sub(r"(?<=[\"'])(https?://.+?)(?=[\"'])", fix_domain_encoding, content)
