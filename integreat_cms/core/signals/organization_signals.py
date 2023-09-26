"""
This module contains signal handlers related to organization objects.
"""

from cacheops import invalidate_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from ...cms.models import Organization, Page, PageTranslation


@receiver(post_save, sender=Organization)
def organization_create_handler(**kwargs):
    r"""
    Invalidate page translation cache after organization creation

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    invalidate_model(Page)
    invalidate_model(PageTranslation)
