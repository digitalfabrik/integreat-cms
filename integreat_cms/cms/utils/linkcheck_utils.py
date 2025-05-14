from __future__ import annotations

import logging
import time
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING
from urllib.parse import quote

from django.conf import settings
from django.db.models import (
    CharField,
    Count,
    F,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import Concat, Replace
from linkcheck import update_lock
from linkcheck.listeners import tasks_queue
from linkcheck.models import Link, Url

from integreat_cms.cms.constants import region_status
from integreat_cms.cms.models import (
    Contact,
    EventTranslation,
    ImprintPageTranslation,
    Organization,
    PageTranslation,
    POITranslation,
    Region,
)

if TYPE_CHECKING:
    from typing import Any

    from ..models import User
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)


def get_urls(
    region_slug: str | None = None,
    url_ids: Any | None = None,
    prefetch_links: bool = False,
) -> list[Url] | QuerySet[Url]:
    """
    Collect all the urls which appear in the latest versions of the contents of the region, filtered by ID or region if given.

    :param region_slug: The slug of the current region
    :param url_ids: The list of requested url ids
    :param prefetch_inks: Whether to prefetch links
    :return: The list (or queryset) of urls
    """
    urls = None
    if url_ids is not None:
        # If the results should be limited to specific ids, filter the queryset
        urls = Url.objects.filter(id__in=url_ids)
    if region_slug:
        regions = Region.objects.filter(slug=region_slug)
    if region_slug is None:
        regions = Region.objects.filter(status=region_status.ACTIVE)

    # Get links from one or mutiple regions and prefetch links
    urls = get_urls_regions(regions, urls, prefetch_links)

    # Temporary: hide all links contained in contacts
    urls = exclude_links_in_contacts(urls, region_slug)

    # Annotate with number of links that are not ignored.
    # If there is any link that is not ignored, the url is also not ignored.
    urls = urls.annotate(
        non_ignored_links=Count("links", filter=Q(links__ignore=False)),
    )

    # Filter out ignored URL types
    if settings.LINKCHECK_IGNORED_URL_TYPES:
        return [
            url for url in urls if url.type not in settings.LINKCHECK_IGNORED_URL_TYPES
        ]

    return urls


def get_urls_regions(
    regions: QuerySet[Region],
    urls: QuerySet[Url] | None = None,
    prefetch_links: bool = False,
) -> QuerySet[Url]:
    """
    Returns the urls of translations of the given regions

    :param regions: The requested objects of Region
    :param urls: If given, prefiltered urls
    :param prefetch_links: Wheter to prefetch links

    :return: A list containing the relevant urls
    """
    regions_links = get_link_query(regions)
    urls = (
        Url.objects.filter(links__in=regions_links).distinct()
        if urls is None
        else urls.filter(links__in=regions_links).distinct()
    )

    # Prefetch all link objects of the requested regions
    if prefetch_links:
        urls = prefetch_regions_links(urls, regions_links)

    return urls


def prefetch_regions_links(
    urls: QuerySet[Url], regions_links: QuerySet[Link]
) -> QuerySet[Url]:
    """
    Returns prefetched Links

    :param urls: urls to attach prefetched links to
    :param regions_links: Queryset of links from requested regions

    :return: urls with prefetched links
    """
    return urls.prefetch_related(
        Prefetch(
            "links",
            queryset=regions_links,
            to_attr="regions_links",
        ),
    )


def exclude_links_in_contacts(
    urls: QuerySet[Url],
    region_slug: str | None = None,
) -> QuerySet[Url]:
    """
    Exclude links contained in contacts from the urls and returns the fitlered urls

    :param urls: urls to be filtered
    :param region_slug: The slug of the current region

    :return: the filtered urls
    """
    # Temporary: hide all links contained in contacts
    if region_slug:
        region = Region.objects.get(slug=region_slug)
    contacts = (
        Contact.objects.filter(location__region=region)
        if region_slug
        else Contact.objects.all()
    )
    contact_links = chain.from_iterable(
        contacts.annotate(
            transformed_email=Concat(
                Value("mailto:"), F("email"), output_field=CharField()
            ),
            transformed_phone=Concat(
                Value("tel:"),
                Replace(F("phone_number"), Value(" (0) "), Value("")),
                output_field=CharField(),
            ),
        ).values_list("transformed_email", "transformed_phone", "website")
    )
    urls = urls.exclude(url__in=contact_links)

    absolute_url_filters = Q()
    for contact in contacts:
        absolute_url_filters |= Q(url__startswith=contact.absolute_url)
        absolute_url_filters |= Q(url=quote(contact.location.map_url, safe="/:&=?,-"))
    return urls.exclude(absolute_url_filters)


def get_link_query(regions: QuerySet[Region]) -> QuerySet:
    """
    Returns the links of translations of the given regions

    :param regions: The requested regions

    :return: A query containing the relevant links
    """
    non_archived_pages = regions[0].non_archived_pages.values("pk")
    for region in regions[1:]:
        # When more than one region is requested, the request comes from the central linkchecker and only active regions should be considered
        if region.status == region_status.ACTIVE:
            non_archived_pages = non_archived_pages.union(
                region.non_archived_pages.values("pk"), all=True
            )
    latest_pagetranslation_versions = Subquery(
        PageTranslation.objects.filter(
            page__id__in=non_archived_pages,
        )
        .distinct("page__id", "language__id")
        .values_list("pk", flat=True),
    )
    latest_poitranslation_versions = Subquery(
        POITranslation.objects.filter(poi__region__in=regions)
        .distinct("poi__id", "language__id")
        .values_list("pk", flat=True),
    )
    latest_eventtranslation_versions = Subquery(
        EventTranslation.objects.filter(event__region__in=regions)
        .distinct("event__id", "language__id")
        .values_list("pk", flat=True),
    )
    latest_imprinttranslation_versions = Subquery(
        ImprintPageTranslation.objects.filter(page__region__in=regions)
        .distinct("page__id", "language__id")
        .values_list("pk", flat=True),
    )
    organizations = Organization.objects.filter(region__in=regions, archived=False)
    # Get all link objects of the requested region
    regions_links = Link.objects.filter(
        page_translation__id__in=latest_pagetranslation_versions,
    ).union(
        Link.objects.filter(
            imprint_translation__id__in=latest_imprinttranslation_versions,
        ),
        Link.objects.filter(event_translation__id__in=latest_eventtranslation_versions),
        Link.objects.filter(poi_translation__id__in=latest_poitranslation_versions),
        Link.objects.filter(organization__id__in=organizations),
        all=True,
    )

    return Link.objects.filter(id__in=regions_links.values("pk")).order_by("id")


def get_url_count(region_slug: str | None = None) -> dict[str, int]:
    """
    Count all urls by status. The content objects are not prefetched because they are not needed for the counter.

    :param region_slug: The slug of the current region

    :return: A dictionary containing the counters of all remaining urls
    """
    _, count_dict = filter_urls(region_slug=region_slug)
    return count_dict


def filter_urls(
    region_slug: str | None = None,
    url_filter: str | None = None,
    prefetch_links: bool = False,
) -> tuple[list[Url], dict[str, int]]:
    """
    Filter all urls of one region by the given category

    :param region_slug: The slug of the current region
    :param url_filter: Which urls should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all urls are returned by default.
    :param prefetch_links: Whether to prefetch region links
    :return: A tuple of the requested urls and a dict containing the counters of all remaining urls
    """
    urls = get_urls(
        region_slug=region_slug,
        prefetch_links=prefetch_links,
    )
    # Split url lists into their respective categories
    ignored_urls, valid_urls, invalid_urls, email_links, phone_links, unchecked_urls = (
        [] for _ in range(6)
    )
    for url in urls:
        if not url.non_ignored_links:
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
                f"Url {url!r} does not fit into any of the defined categories",
            )
    # Pass the number of urls to a dict which can be used as extra template context
    count_dict = get_url_numbers_dict(
        urls,
        valid_urls,
        unchecked_urls,
        ignored_urls,
        invalid_urls,
        email_links,
        phone_links,
    )
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


def get_url_numbers_dict(
    urls: list[Url],
    valid_urls: list[Url],
    unchecked_urls: list[Url],
    ignored_urls: list[Url],
    invalid_urls: list[Url],
    email_links: list[Url],
    phone_links: list[Url],
) -> dict:
    """
    Pass the number of urls to a dict which can be used as extra template context

    :param urls: List of all urls
    :param valid_urls: List of all valid urls
    :param unchecked_urls: List of all unchecked urls
    :param ignored_urls: List of all ignored urls
    :param invalid_rls: List of all ignored urls
    :param email_links: List of all email links
    :param phone_links: List of all phone links

    :return: A dict containing numbers of urls
    """
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
    return count_dict


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
    log_replacement_is_starting(search, replace, region, user)
    content_objects = find_target_url_per_content(search, replace, region, link_types)
    with update_lock:
        for content, urls_to_replace in content_objects.items():
            content.replace_urls(urls_to_replace, user, commit)

    # Wait until all post-save signals have been processed
    logger.debug("Waiting for linkcheck listeners to update link database...")
    time.sleep(0.1)
    tasks_queue.join()
    logger.info("Finished replacing %r with %r in content links", search, replace)


def find_target_url_per_content(
    search: str,
    replace: str,
    region: Region | None,
    link_types: list[str] | None,
) -> dict[AbstractContentTranslation, dict[str, str]]:
    """
    returns in which translation what URL must be replaced

    :param search: The (partial) URL to search
    :param replace: The (partial) URL to replace
    :param region: Optionally limit the replacement to one region (``None`` means a global replacement)
    :param link_types: Which kind of links should be replaced

    :return: A dictionary of translations and list of before&after of ULRs
    """
    # This function is used in replace_links, which is used in the management command, where region can be None, too.
    # However get_link_query currently requires a valid region.
    # Collect all the link objects in case no region is given.
    if region:
        region_query_set = Region.objects.filter(slug=region.slug)
    links = (
        (get_link_query(region_query_set) if region else Link.objects.all())
        .filter(url__url__contains=search)
        .select_related("url")
    )

    links_to_replace = (
        (
            link
            for link in links
            if link.url.type in link_types
            or (link.url.status is False and "invalid" in link_types)
        )
        if link_types
        else links
    )

    content_objects: defaultdict[AbstractContentTranslation, dict[str, str]] = (
        defaultdict(dict)
    )
    for link in links_to_replace:
        content_objects[link.content_object][link.url.url] = link.url.url.replace(
            search,
            replace,
        )
    return content_objects


def log_replacement_is_starting(
    search: str,
    replace: str,
    region: Region | None,
    user: User | None,
) -> None:
    """
    function to log the current link replacement

    :param search: The (partial) URL to search
    :param replace: The (partial) URL to replace
    :param region: Optionally limit the replacement to one region (``None`` means a global replacement)
    :param user: The creator of the replaced translations
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
