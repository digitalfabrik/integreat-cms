"""
This module contains signal handlers related to the cache.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.cache import cache
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import Any


@receiver(post_migrate)
def flush_cache_after_migrate(*args: Any, **kwargs: Any) -> None:
    cache.clear()
    logger.debug("Cache flushed after post_migrate call.")
