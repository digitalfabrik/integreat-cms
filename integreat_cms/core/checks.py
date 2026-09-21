from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.core.checks import Error, register

from ..cms.constants import machine_translation_providers

if TYPE_CHECKING:
    from typing import Any

    from django.apps.config import AppConfig


@register()
def check_redis_reachable(
    app_configs: list[AppConfig] | None,  # noqa: ARG001 — required by Django's check signature
    **kwargs: Any,
) -> list[Error]:
    """
    ``IGNORE_EXCEPTIONS`` on the Redis cache backend means a broken
    connection degrades silently (cache reads/writes become no-ops) instead
    of raising - so an unreachable Redis when :setting:`REDIS_CACHE` is
    enabled must be caught here via a round trip, not by relying on an
    exception.
    """
    if not settings.REDIS_CACHE:
        return []

    probe_key = f"redis_reachability_check_{uuid.uuid4()}"
    cache.set(probe_key, "ok", timeout=5)
    if cache.get(probe_key) != "ok":
        return [
            Error(
                "Redis is enabled (INTEGREAT_CMS_REDIS_CACHE=True) but not reachable.",
                hint=(
                    "Check that Redis is running and that "
                    "INTEGREAT_CMS_REDIS_UNIX_SOCKET or INTEGREAT_CMS_REDIS_HOST/"
                    "INTEGREAT_CMS_REDIS_PORT point to it."
                ),
                id="core.E001",
            ),
        ]
    return []


def mt_locking_requires_redis() -> bool:
    """
    Whether the current settings put the machine translation locking
    mechanism (see :func:`~integreat_cms.core.utils.machine_translation_celery_task.acquire_locks`)
    at risk of silently becoming a no-op.

    That lock is just a Django cache entry. Without :setting:`REDIS_CACHE`,
    the cache falls back to a per-process ``LocMemCache`` (see
    :setting:`CACHES`), which only behaves like a real lock when Celery
    tasks run in the same process as the code that queues them, i.e. when
    :setting:`CELERY_TASK_ALWAYS_EAGER` is set (as it is in tests).
    """
    return (
        not settings.REDIS_CACHE
        and not getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)
        and any(provider.enabled for provider in machine_translation_providers.CHOICES)
    )


@register()
def check_mt_lock_backend(
    app_configs: list[AppConfig] | None,  # noqa: ARG001 — required by Django's check signature
    **kwargs: Any,
) -> list[Error]:
    """
    Machine translation relies on a cache-based lock to stop the same
    object/language from being translated twice concurrently. That lock only
    works across processes when it is backed by Redis - without it (and
    without :setting:`CELERY_TASK_ALWAYS_EAGER`, which keeps everything in
    one process), it silently degrades to a per-process, per-worker lock.
    """
    if mt_locking_requires_redis():
        return [
            Error(
                "Machine translation is enabled but Redis is disabled "
                "(INTEGREAT_CMS_REDIS_CACHE=False), and Celery tasks are not "
                "eager. The machine translation locking mechanism requires a "
                "cache shared across processes and will not prevent "
                "concurrent translations of the same content.",
                hint=(
                    "Enable Redis (INTEGREAT_CMS_REDIS_CACHE=True), or set "
                    "CELERY_TASK_ALWAYS_EAGER=True if tasks are intentionally "
                    "run in-process."
                ),
                id="core.E002",
            ),
        ]
    return []
