from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..places.place_translation import PlaceTranslation
from .feedback import Feedback

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class PlaceFeedback(Feedback):
    """
    Database model representing feedback about events.
    """

    place_translation = models.ForeignKey(
        PlaceTranslation,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("place translation"),
    )

    @property
    def object_name(self) -> str:
        """
        This property returns the name of the object this feedback comments on.

        :return: The name of the object this feedback refers to
        """
        return self.best_place_translation.title

    @cached_property
    def object_url(self) -> str:
        """
        This property returns the url to the object this feedback comments on.

        :return: The url to the referred object
        """
        return reverse(
            "edit_place",
            kwargs={
                "place_id": self.place_translation.place.id,
                "region_slug": self.region.slug,
                "language_slug": self.best_place_translation.language.slug,
            },
        )

    @cached_property
    def best_place_translation(self) -> PlaceTranslation:
        """
        This property returns the best translation for the Place this feedback comments on.

        :return: The best place translation
        """
        return self.place_translation.place.best_translation

    @property
    def related_feedback(self) -> QuerySet[PlaceFeedback]:
        """
        This property returns all feedback entries which relate to the same object and have the same is_technical value.

        :return: The queryset of related feedback
        """
        return PlaceFeedback.objects.filter(
            place_translation__place=self.place_translation.place,
            language=self.language,
            is_technical=self.is_technical,
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("place feedback")
        #: The plural verbose name of the model
        verbose_name_plural = _("place feedback")
        #: The default permissions for this model
        default_permissions = ()
