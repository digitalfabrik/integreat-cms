import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from linkcheck.models import Link

from .abstract_base_page_translation import AbstractBasePageTranslation


logger = logging.getLogger(__name__)


class ImprintPageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a imprint translation
    """

    page = models.ForeignKey(
        "cms.ImprintPage",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("imprint"),
    )

    links = GenericRelation(Link, related_query_name="imprint_translation")

    @cached_property
    def url_infix(self):
        """
        Generates the infix of the url of the imprint translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        :rtype: str
        """
        return ""

    @cached_property
    def backend_edit_link(self):
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        :rtype: str
        """
        return reverse(
            "edit_imprint",
            kwargs={
                "language_slug": self.language.slug,
                "region_slug": self.page.region.slug,
            },
        )

    @cached_property
    def short_url(self):
        """
        This function returns the absolute short url to the imprint translation

        :return: The short url of an imprint translation
        :rtype: str
        """

        return settings.BASE_URL + reverse(
            "public:expand_imprint_translation_id",
            kwargs={"imprint_translation_id": self.id},
        )

    @property
    def slug(self):
        """
        For compatibility with the other page translations, a slug property is useful.

        :return: pseudo slug for the imprint translation
        :rtype: str
        """
        return settings.IMPRINT_SLUG

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprint translations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "imprint_translations"
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page__pk", "language__pk", "-version"]
        #: A list of database constraints for this model
        constraints = [
            models.UniqueConstraint(
                fields=["page", "language", "version"],
                name="%(class)s_unique_version",
            ),
        ]
