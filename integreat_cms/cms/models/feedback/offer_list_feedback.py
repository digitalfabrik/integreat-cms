from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .feedback import Feedback


class OfferListFeedback(Feedback):
    """
    Database model representing feedback about the offer list (e.g. missing offers).
    """

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return _("Offer List")

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse(
            "offertemplates",
        )

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.offer_list_feedback.OfferListFeedback ]
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
