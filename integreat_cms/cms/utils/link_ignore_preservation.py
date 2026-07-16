"""
Carry editor-set ``Link.ignore`` flags across the delete-and-recreate
cycle that runs on every translation save.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from . import internal_link_utils

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..models.abstract_content_translation import AbstractContentTranslation


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
