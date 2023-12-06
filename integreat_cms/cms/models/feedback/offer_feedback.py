from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..offers.offer_template import OfferTemplate
from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class OfferFeedback(Feedback):
    """
    Database model representing feedback about offers.
    """

    offer = models.ForeignKey(
        OfferTemplate,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("offer"),
    )

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return self.offer.name

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse("edit_offertemplate", kwargs={"slug": self.offer.slug})

    @property
    def related_feedback(self) -> QuerySet[OfferFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return OfferFeedback.objects.filter(
            offer=self.offer, is_technical=self.is_technical
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("offer feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("offer feedback")
        #: The default permissions for this model
        default_permissions = ()
