from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..pages.imprint_page import ImprintPage
from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class ImprintPageFeedback(Feedback):
    """
    Database model representing feedback about imprint pages.
    """

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        try:
            translation = (
                self.region.imprint.get_translation(self.language.slug)
                or self.region.imprint.default_translation
            )
            return translation
        except ImprintPage.DoesNotExist:
            return _("Imprint")

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse(
            "edit_imprint",
            kwargs={
                "region_slug": self.region.slug,
                "language_slug": self.language.slug,
            },
        )

    @property
    def related_feedback(self) -> QuerySet[ImprintPageFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return ImprintPageFeedback.objects.filter(
            region=self.region, language=self.language, is_technical=self.is_technical
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprint feedback")
        #: The default permissions for this model
        default_permissions = ()
