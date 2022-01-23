from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback
from ..offers.offer_template import OfferTemplate


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
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return self.offer.name

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse("edit_offertemplate", kwargs={"slug": self.offer.slug})

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.offer_feedback.OfferFeedback ]
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
