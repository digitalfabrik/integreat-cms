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

    latest_version = instance.latest_version

    if (
        latest_version
        and latest_version.hix_score
        and latest_version.content == instance.content
    ):
        logger.debug(
            "Content of %r was not changed, copying the HIX score from the previous version: %r",
            instance,
            latest_version.hix_score,
        )
        instance.hix_score = latest_version.hix_score
        return

    if score := lookup_hix_score(instance.content):
        logger.debug("Storing hix score %s for %r", score, instance)
        instance.hix_score = score
    else:
        logger.warning("Could not store the hix score for %r", instance)
