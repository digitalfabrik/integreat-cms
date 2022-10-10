from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..languages.language import Language
from .poi_category import POICategory


class POICategoryTranslation(AbstractBaseModel):
    """
    Data model representing a POI category translation.
    """

    category = models.ForeignKey(
        POICategory,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("category"),
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="poi_category_translations",
        verbose_name=_("language"),
    )
    name = models.CharField(
        max_length=250,
        verbose_name=_("category name"),
        help_text=_("The name of the POI category."),
    )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``POICategoryTranslation object (name)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the category translation
        :rtype: str
        """
        return self.name

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<POI CategoryTranslation: POICategoryTranslation object (id, category name)>``.
        It is used for logging.

        :return: The canonical string representation of the category translation
        :rtype: str
        """
        return f"<POI CategoryTranslation (id: {self.id}, category: {self.category_id}, language: {self.language_id}, name: {self.name})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location category translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("location category translations")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The default sorting for this model
        ordering = ["category"]
