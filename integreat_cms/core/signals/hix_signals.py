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

    content_unchanged = (
        instance.latest_version
        and instance.latest_version.content == instance.content
        and instance.latest_version.hix_score is not None
    )
    if (
        instance.hix_score
        or instance.hix_ignore
        or not instance.hix_enabled
        or not instance.content.strip()
        or content_unchanged
    ):
        logger.debug(
            "HIX calculation pre save signal skipped for %r (score=%s, ignored=%s, enabled=%s, empty=%s, unchanged=%s)",
            instance,
            instance.hix_score,
            instance.hix_ignore,
            instance.hix_enabled,
            not bool(instance.content.strip()),
            content_unchanged,
        )
        instance.hix_score = (
            instance.latest_version.hix_score if content_unchanged else None
        )
        return

    if score := lookup_hix_score(instance.content):
        logger.debug("Storing hix score %s for %r", score, instance)
        instance.hix_score = score
    else:
        logger.warning("Could not store the hix score for %r", instance)
