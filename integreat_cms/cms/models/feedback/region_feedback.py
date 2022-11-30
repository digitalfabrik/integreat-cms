from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .feedback import Feedback


class RegionFeedback(Feedback):
    """
    Database model representing feedback about regions in general.
    """

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return self.region.name

    @cached_property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse(
            "dashboard",
            kwargs={
                "region_slug": self.region.slug,
            },
        )

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.feedback.region_feedback.RegionFeedback ]
        """
        return RegionFeedback.objects.filter(
            region=self.region, language=self.language, is_technical=self.is_technical
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("region feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("region feedback")
        #: The default permissions for this model
        default_permissions = ()
