import logging
import time
from copy import deepcopy
from functools import partial

from django.conf import settings
from django.db.models import Prefetch, Q
from linkcheck import update_lock
from linkcheck.listeners import tasks_queue
from linkcheck.models import Link, Url
from lxml.html import rewrite_links

from integreat_cms.cms.models import EventTranslation, PageTranslation, POITranslation

logger = logging.getLogger(__name__)


def get_urls(region_slug=None, url_ids=None, prefetch_content_objects=True):
    """
    Count all urls by status, either of a specific region or globally

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param url_ids: The list of requested url ids
    :type url_ids: list

    :param prefetch_content_objects: Whether or not content objects should be prefetched
    :type prefetch_content_objects: bool

    :return: The list (or queryset) of urls
    :rtype: list or ~django.db.models.query.QuerySet
    """
    urls = Url.objects.all()
    if url_ids is not None:
        # If the results should be limited to specific ids, filter the queryset
        urls = urls.filter(id__in=url_ids)
    if region_slug:
        # Get all link objects of the requested region
        region_links = Link.objects.filter(
            Q(page_translation__page__region__slug=region_slug)
            | Q(imprint_translation__page__region__slug=region_slug)
            | Q(event_translation__event__region__slug=region_slug)
            | Q(poi_translation__poi__region__slug=region_slug)
        ).order_by("id")
        if prefetch_content_objects:
            region_links = region_links.prefetch_related("content_object")
        # Prefetch all link objects of the requested region
        urls = urls.prefetch_related(
            Prefetch(
                "links",
                queryset=region_links,
                to_attr="region_links",
            )
        )
    elif prefetch_content_objects:
        urls = urls.prefetch_related("links__content_object")
    # Filter out ignored URL types
    urls = [url for url in urls if url.type not in settings.LINKCHECK_IGNORED_URL_TYPES]
    if region_slug:
        # If the region slug is given, only return urls that occur at least once in the requested region
        urls = [url for url in urls if url.region_links]
    return urls


def get_url_count(region_slug=None):
    """
    Count all urls by status. The content objects are not prefetched because they are not needed for the counter.

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: A dictionary containing the counters of all remaining urls
    :rtype: dict
    """
    _, count_dict = filter_urls(region_slug=region_slug, prefetch_content_objects=False)
    return count_dict


# pylint: disable=too-many-branches
def filter_urls(region_slug=None, url_filter=None, prefetch_content_objects=True):
    """
    Filter all urls of one region by the given category

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param url_filter: Which urls should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all urls are returned by default.
    :type url_filter: str

    :param prefetch_content_objects: Whether or not content objects should be prefetched
    :type prefetch_content_objects: bool

    :return: A tuple of the requested urls and a dict containing the counters of all remaining urls
    :rtype: tuple
    """
    urls = get_urls(
        region_slug=region_slug, prefetch_content_objects=prefetch_content_objects
    )
    # Split url lists into their respective categories
    ignored_urls, valid_urls, invalid_urls, email_links, phone_links, unchecked_urls = (
        [] for i in range(6)
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


def replace_link_helper(old_url, new_url, link):
    """
    A small helper function which can be passed to :meth:`lxml.html.HtmlMixin.rewrite_links`

    :param old_url: The url which should be replaced
    :type old_url: str

    :param new_url: The url which should be inserted instead of the old url
    :type new_url: str

    :param link: The current link
    :type link: str

    :return: The replaced link
    :rtype: str
    """
    return new_url if link == old_url else link


def save_new_version(translation, new_translation, user):
    """
    Save a new translation version

    :param translation: The old translation
    :type translation: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation

    :param new_translation: The new translation
    :type new_translation: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation

    :param user: The creator of the new version
    :type user: ~integreat_cms.cms.models.users.user.User
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
    search, replace, region=None, user=None, commit=True, link_types=None
):
    """
    Perform search & replace in the content links

    :param search: The (partial) URL to search
    :type search: str

    :param replace: The (partial) URL to replace
    :type replace: str

    :param region: Optionally limit the replacement to one region (``None`` means a global replacement)
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param user: The creator of the replaced translations
    :type user: ~integreat_cms.cms.models.users.user.User

    :param commit: Whether changes should be written to the database
    :type commit: bool

    :param link_types: Which kind of links should be replaced
    :type link_types: list

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
            filters = {f"{model.foreign_field()}__region": region} if region else {}
            for translation in model.objects.filter(**filters).distinct(
                model.foreign_field(), "language"
            ):
                new_translation = deepcopy(translation)
                for link in translation.links.select_related("url"):
                    url = link.url.url
                    if search in url and (
                        not link_types or link.url.type in link_types
                    ):
                        fixed_url = url.replace(search, replace)
                        new_translation.content = rewrite_links(
                            new_translation.content,
                            partial(replace_link_helper, url, fixed_url),
                        )
                        logger.debug(
                            "Replacing %r with %r in %r", url, fixed_url, translation
                        )
                if new_translation.content != translation.content and commit:
                    save_new_version(translation, new_translation, user)
    # Wait until all post-save signals have been processed
    logger.debug("Waiting for linkcheck listeners to update link database...")
    time.sleep(0.1)
    tasks_queue.join()
    logger.info("Finished replacing %r with %r in content links", search, replace)
