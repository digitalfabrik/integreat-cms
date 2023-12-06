"""
This module contains signal handlers related to organization objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cacheops import invalidate_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from ...cms.models import Organization, Page, PageTranslation

if TYPE_CHECKING:
    from typing import Any


@receiver(post_save, sender=Organization)
def organization_create_handler(**kwargs: Any) -> None:
    r"""
    Invalidate page translation cache after organization creation

    :param \**kwargs: The supplied keyword arguments
    """
    invalidate_model(Page)
    invalidate_model(PageTranslation)
