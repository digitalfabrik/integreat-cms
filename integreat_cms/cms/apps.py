from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.db.models import Model
    from django.utils.functional import Promise
    from linkcheck import Linklist

logger = logging.getLogger(__name__)


class CmsConfig(AppConfig):
    """
    This class represents the Django-configuration of the backend.

    See :class:`django.apps.AppConfig` for more information.

    :param name: The name of the app
    """

    #: Full Python path to the application
    name: Final[str] = "integreat_cms.cms"
    #: Human-readable name for the application
    verbose_name: Final[Promise] = _("CMS")

    def ready(self) -> None:
        from django.core.cache import cache
        from linkcheck import celery as linkcheck_celery
        from linkcheck import listeners as linkcheck_listeners
        from linkcheck import worker_tasks as linkcheck_worker_tasks
        from linkcheck.models import Link, Url

        from .models.abstract_content_translation import AbstractContentTranslation
        from .utils.internal_link_checker import check_internal
        from .utils.link_ignore_preservation import cache_key_for, target_key

        Url.check_internal = check_internal

        # Reapply ignore=True to Link rows that were stashed by a
        # preserve_ignored_links context manager at the delete site.
        upstream = linkcheck_worker_tasks.do_check_instance_links

        def do_check_instance_links_preserving_ignore(
            sender: type[Model],
            instance: Model,
            linklist_cls: type[Linklist],
            wait: bool = False,
        ) -> None:
            cache_key = (
                cache_key_for(instance)
                if isinstance(instance, AbstractContentTranslation)
                else None
            )
            stashed = cache.get(cache_key) if cache_key else None
            upstream(sender, instance, linklist_cls, wait=wait)
            if stashed:
                ignored_keys = {tuple(k) for k in stashed}
                cache.delete(cache_key)
                to_re_ignore = [
                    link.pk
                    for link in Link.objects.filter(
                        content_type=linklist_cls.content_type(),
                        object_id=instance.pk,
                    ).select_related("url")
                    if target_key(link.url.url) in ignored_keys
                ]
                if to_re_ignore:
                    Link.objects.filter(pk__in=to_re_ignore).update(ignore=True)

        # Patch all three references — listeners and celery imported the
        # name at module load.
        linkcheck_worker_tasks.do_check_instance_links = (
            do_check_instance_links_preserving_ignore
        )
        linkcheck_listeners.do_check_instance_links = (
            do_check_instance_links_preserving_ignore
        )
        linkcheck_celery.do_check_instance_links = (
            do_check_instance_links_preserving_ignore
        )
