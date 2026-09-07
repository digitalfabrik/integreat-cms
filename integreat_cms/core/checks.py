from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.core.checks import Error, register

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
