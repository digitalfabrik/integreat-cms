from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class RegionFeedback(Feedback):
    """
    Database model representing feedback about regions in general.
    """

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return self.region.name

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse(
            "dashboard",
            kwargs={
                "region_slug": self.region.slug,
            },
        )

    @property
    def related_feedback(self) -> QuerySet[RegionFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return RegionFeedback.objects.filter(
            region=self.region,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("region feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("region feedback")
        #: The default permissions for this model
        default_permissions = ()
