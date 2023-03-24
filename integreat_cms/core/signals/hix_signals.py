import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from ...cms.models import PageTranslation
from ...cms.views.utils.hix import lookup_hix_score

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PageTranslation)
def page_translation_save_handler(instance, **kwargs):
    r"""
    Calculates a hix store for a page translation after saving

    :param instance: The page translation that gets saved
    :type instance: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict
    """
    if (
        kwargs.get("raw")
        or instance.hix_score
        or not hix_enabled(instance)
        or not instance.content.strip()
    ):
        return

    if score := lookup_hix_score(instance.content):
        logger.debug(
            "Storing hix score %s for new page translation %r", score, instance
        )
        instance.hix_score = score
        instance.save(update_timestamp=False)
    else:
        logger.warning(
            "Could not store the hix score for new page translation %r", instance
        )


def hix_enabled(instance):
    """
    This function returns whether the hix api is enabled for this instance

    :param instance: The page translation to check for
    :type instance: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :returns: Whether hix is enabled
    :rtype: bool
    """
    return (
        settings.TEXTLAB_API_ENABLED
        and instance.language.slug in settings.TEXTLAB_API_LANGUAGES
        and instance.page.region.hix_enabled
    )
