from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class OfferListFeedback(Feedback):
    """
    Database model representing feedback about the offer list (e.g. missing offers).
    """

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return _("Offer List")

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse(
            "offertemplates",
        )

    @property
    def related_feedback(self) -> QuerySet[OfferListFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return OfferListFeedback.objects.filter(
            region=self.region, language=self.language, is_technical=self.is_technical
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer list feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("offer list feedback")
        #: The default permissions for this model
        default_permissions = ()
