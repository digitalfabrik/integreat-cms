import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from ...cms.models import PageTranslation
from ...cms.views.utils.hix import lookup_hix_score

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=PageTranslation)
def page_translation_save_handler(instance, **kwargs):
    r"""
    Calculates a hix store for a page translation before saving

    :param instance: The page translation that gets saved
    :type instance: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """

    if kwargs.get("raw"):
        return

    if instance.hix_ignore or not instance.hix_enabled or not instance.content.strip():
        logger.debug(
            "HIX calculation pre save signal skipped for %r (ignored=%s, enabled=%s, empty=%s)",
            instance,
            instance.hix_ignore,
            instance.hix_enabled,
            not bool(instance.content.strip()),
        )
        instance.hix_score = None
        return

    if identical_version := instance.all_versions.filter(
        content=instance.content, hix_score__isnull=False
    ).first():
        logger.debug(
            "Content of %r is identical to %r, copying HIX score %r",
            instance,
            identical_version,
            identical_version.hix_score,
        )
        instance.hix_score = identical_version.hix_score
        return

    if score := lookup_hix_score(instance.content):
        logger.debug("Storing hix score %s for %r", score, instance)
        instance.hix_score = score
    else:
        logger.warning("Could not store the hix score for %r", instance)
