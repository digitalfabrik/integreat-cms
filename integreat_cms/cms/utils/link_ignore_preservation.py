"""
Carry editor-set ``Link.ignore`` flags across the delete-and-recreate
cycle that runs on every translation save.
"""

from __future__ import annotations

import operator
from contextlib import contextmanager
from functools import reduce
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Model, Q
from linkcheck.models import Link

from . import internal_link_utils

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.db.models import QuerySet

    from ..models.abstract_content_translation import AbstractContentTranslation
    from ..models.regions.region import Region


_CACHE_TTL = 600
_CACHE_PREFIX = "linkcheck_pending_ignore"


def target_key(url_string: str) -> tuple[str, object]:
    """
    Stable identity for a URL's target. Internal URLs that resolve to a
    content object share a key across slug rewrites; everything else
    falls back to the URL string.
    """
    resolved = internal_link_utils.get_public_translation_for_link(url_string)
    if resolved is None:
        return ("ext", url_string)
    return (type(resolved).__name__, resolved.foreign_object.pk)


def cache_key_for(translation: AbstractContentTranslation) -> str:
    foreign = translation.foreign_object
    foreign_ct = ContentType.objects.get_for_model(foreign)
    return f"{_CACHE_PREFIX}:{foreign_ct.id}:{foreign.pk}:{translation.language_id}"


@contextmanager
def preserve_ignored_links(
    translation: AbstractContentTranslation,
) -> Iterator[None]:
    """
    Snapshot target-keys of ignored Links on ``translation`` so the next
    ``do_check_instance_links`` for the same (foreign_object, language)
    can restore the flag on the freshly reconciled Links.

    Wrap the delete-and-save sequence:

        with preserve_ignored_links(self):
            self.links.all().delete()
            new_translation.save()

    The follow-up reconciliation may run synchronously or via Celery on
    transaction commit; the stash is shared via the Django cache so both
    paths see it.
    """
    keys = [
        target_key(link.url.url)
        for link in translation.links.filter(ignore=True).select_related("url")
    ]
    if keys:
        cache.set(cache_key_for(translation), keys, timeout=_CACHE_TTL)
    yield


def region_of(instance: Model) -> Region | None:
    """
    The region an instance's links belong to, or ``None`` if it cannot be
    determined. Content translations derive it from their foreign object;
    organizations carry it directly.
    """
    # Local import to avoid a circular import at module load time.
    from ..models.abstract_content_translation import AbstractContentTranslation

    if isinstance(instance, AbstractContentTranslation):
        return instance.foreign_object.region
    return getattr(instance, "region", None)


def inherit_ignore_within_region(
    instance: Model,
    content_type: ContentType,
    region: Region | None,
) -> None:
    """
    Carry the ``Link.ignore`` flag onto freshly reconciled links of
    *instance* whose URL is already marked ignored on another current link
    of the *same region*.

    This complements :func:`preserve_ignored_links`: the context manager
    only restores the flag across the delete-and-recreate cycle of a single
    content object, whereas this keeps a URL an editor already marked as
    verified from re-surfacing as unverified when the very same URL appears
    in a *different* (or newly created) content object of the region.

    Inheritance is deliberately region-scoped: a URL verified in one region
    must not silently suppress the same URL in another region whose editors
    never vetted it.
    """
    if region is None:
        return

    # URLs that this instance links to but which are not (yet) ignored here
    pending_url_ids = set(
        Link.objects.filter(
            content_type=content_type,
            object_id=instance.pk,
            ignore=False,
        ).values_list("url_id", flat=True)
    )
    if not pending_url_ids:
        return

    already_ignored_url_ids = set(
        _region_links(region)
        .filter(url_id__in=pending_url_ids, ignore=True)
        .exclude(content_type=content_type, object_id=instance.pk)
        .values_list("url_id", flat=True)
    )
    if not already_ignored_url_ids:
        return

    Link.objects.filter(
        content_type=content_type,
        object_id=instance.pk,
        ignore=False,
        url_id__in=already_ignored_url_ids,
    ).update(ignore=True)


def _region_links(region: Region) -> QuerySet[Link]:
    """
    All links whose content object belongs to the given region, across every
    linkchecked model, excluding archived content.

    Archived pages/events/POIs/organizations are hidden from the broken-links
    dashboard, so a URL that is only verified there must not suppress the same
    URL on live content. Archiving works differently per model:

    * pages are archived via the tree (``Region.non_archived_pages`` accounts
      for both explicitly archived pages and descendants of archived ones);
    * events, POIs and organizations carry a plain ``archived`` flag;
    * imprint pages have no archived state.
    """
    branches = [
        Q(page_translation__page__in=region.non_archived_pages.values("pk")),
        Q(imprint_translation__page__region=region),
        Q(
            event_translation__event__region=region,
            event_translation__event__archived=False,
        ),
        Q(
            poi_translation__poi__region=region,
            poi_translation__poi__archived=False,
        ),
        Q(organization__region=region, organization__archived=False),
    ]
    return Link.objects.filter(reduce(operator.or_, branches))
