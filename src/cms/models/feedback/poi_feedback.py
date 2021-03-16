from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from ..pois.poi_translation import POITranslation
from .feedback import Feedback


class POIFeedback(Feedback):
    """
    Database model representing feedback about events.
    """

    poi_translation = models.ForeignKey(
        POITranslation,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("location translation"),
    )

    @property
    def object_name(self):
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        :rtype: str
        """
        return self.poi_translation.poi.best_translation.title

    @property
    def object_url(self):
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        :rtype: str
        """
        return reverse(
            "edit_poi",
            kwargs={
                "poi_id": self.poi_translation.poi.id,
                "region_slug": self.region.slug,
                "language_slug": self.poi_translation.poi.best_translation.language.slug,
            },
        )

    @property
    def related_feedback(self):
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        :rtype: ~django.db.models.query.QuerySet [ ~cms.models.feedback.poi_feedback.POIFeedback ]
        """
        return POIFeedback.objects.filter(
            poi_translation__poi=self.poi_translation.poi,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("location feedback")
        #: The default permissions for this model
        default_permissions = ()
