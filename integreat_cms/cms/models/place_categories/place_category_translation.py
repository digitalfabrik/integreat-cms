from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from .place_category import PlaceCategory


class PlaceCategoryTranslation(AbstractBaseModel):
    """
    Data model representing a Place category translation.
    """

    category = models.ForeignKey(
        PlaceCategory,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("category"),
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="place_category_translations",
        verbose_name=_("language"),
    )
    name = models.CharField(
        max_length=250,
        verbose_name=_("category name"),
        help_text=_("The name of the place category."),
    )

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PlaceCategoryTranslation object (name)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the category translation
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Place CategoryTranslation: PlaceCategoryTranslation object (id, category name)>``.
        It is used for logging.

        :return: The canonical string representation of the category translation
        """
        class_name = type(self).__name__
        if not self.pk:
            return f"<{class_name} (unsaved instance)>"
        return f"<Place CategoryTranslation (id: {self.id}, category: {self.category_id}, language: {self.language_id}, name: {self.name})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("place category translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("place category translations")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The default sorting for this model
        ordering = ["category"]
