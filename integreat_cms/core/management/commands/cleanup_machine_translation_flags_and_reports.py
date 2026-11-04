from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from cacheops import invalidate_obj
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from ....cms.constants import async_machine_translation
from ....cms.models import MachineTranslationReport
from ...utils.machine_translation_celery_task import get_mt_redis_lock_key
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

#: Machine translation reports which were not fetched by their user within this time are deleted
REPORT_EXPIRATION = timedelta(days=30)


class Command(LogCommand):
    """
    Management command to clean up machine translation state which was left behind, e.g. by a crashed Celery worker
    """

    help: str = (
        "Clear machine translation flags whose lock does not exist anymore "
        "and delete expired machine translation reports"
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.set_logging_stream()

        if not settings.REDIS_CACHE:
            raise CommandError(
                "The machine translation locks can only be checked from a separate process if Redis is enabled.",
            )

        num_cleared_flags = sum(
            self.clear_stale_flags(content_type)
            for content_type in async_machine_translation.CONTENT_TYPES
        )
        num_deleted_reports, _ = MachineTranslationReport.objects.filter(
            created_at__lt=timezone.now() - REPORT_EXPIRATION,
        ).delete()

        logger.success(  # type: ignore[attr-defined]
            "✔ Cleared %d stale machine translation flag(s) and deleted %d expired machine translation report(s).",
            num_cleared_flags,
            num_deleted_reports,
        )

    @staticmethod
    def clear_stale_flags(content_type: str) -> int:
        """
        Clear the ``currently_in_machine_translation`` flag of all translations whose machine translation lock does
        not exist anymore. The lock is acquired before the flag is set and released before the flag is cleared, so a
        flag without lock means that the task which set it died before it could clean up after itself.

        :param content_type: The content type whose translations should be checked
        :return: The number of cleared flags
        """
        translation_model = apps.get_model("cms", f"{content_type}translation")
        with transaction.atomic():
            # Locking the rows bypasses cacheops and makes a concurrently queued task wait with setting its
            # flag until this transaction is committed, so a flag can't be cleared right after it was set
            flagged_translations = (
                translation_model.objects.filter(currently_in_machine_translation=True)
                .select_related("language")
                .select_for_update(of=("self",))
            )
            lock_keys = {
                translation: get_mt_redis_lock_key(
                    content_type,
                    getattr(translation, f"{translation.foreign_field()}_id"),
                    translation.language.slug,
                )
                for translation in flagged_translations
            }
            locks = cache.get_many(lock_keys.values())
            stale_translations = [
                translation
                for translation, lock_key in lock_keys.items()
                if lock_key not in locks
            ]
            for translation in stale_translations:
                logger.info(
                    "Clearing stale machine translation flag of %r", translation
                )
            translation_model.objects.filter(
                id__in=[translation.id for translation in stale_translations],
            ).update(currently_in_machine_translation=False)
        # A plain update() bypasses cacheops, so the cached queries have to be invalidated manually
        for translation in stale_translations:
            invalidate_obj(translation)
        return len(stale_translations)
