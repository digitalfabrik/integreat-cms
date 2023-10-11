from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from .poi_category_translation import POICategoryTranslation

from ...constants import poicategory
from ..abstract_base_model import AbstractBaseModel


class POICategory(AbstractBaseModel):
    """
    Data model representing a POI category.
    """

    icon = models.CharField(
        choices=poicategory.ICONS,
        max_length=256,
        verbose_name=_("icon"),
        blank=True,
        null=True,
        help_text=_("Select an icon for this category"),
    )

    color = models.CharField(
        choices=poicategory.COLORS,
        max_length=7,
        verbose_name=_("color"),
        blank=True,
        null=True,
        help_text=_("Select a color for map pins with this category"),
    )

    @cached_property
    def name(self) -> str:
        """
        This function returns the name of the category in the "best" translation

        :return: The name of the category
        """
        return (
            self.best_translation.name
            if self.best_translation
            else str(_("POI category"))
        )

    @cached_property
    def prefetched_translations_by_language_slug(
        self,
    ) -> dict[str, POICategoryTranslation]:
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return {
            translation.language.slug: translation
            for translation in self.translations.all()
        }

    def get_translation(self, language_slug: str) -> POICategoryTranslation | None:
        """
        Get the translation of this category in a given language

        :param language_slug: language in which the poi category is to be shown
        :return: translation of the poi category in the language
                 if no translation is saved for the language, the category name of the POICategory
        """
        return self.prefetched_translations_by_language_slug.get(language_slug)

    @cached_property
    def backend_translation(self) -> POICategoryTranslation | None:
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        """
        return self.get_translation(get_language())

    @cached_property
    def best_translation(self) -> POICategoryTranslation:
        """
        This function returns the translation of this category in the current backend language and if it doesn't
        exist, it provides a fallback to the first translation.

        :return: The "best" translation of this category for displaying in the backend
        """
        return self.backend_translation or self.translations.first()

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``POICategory object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the category
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<POI Category: POICategory object (id, category name)>``.
        It is used for logging.

        :return: The canonical string representation of the category
        """
        return f"<POI Category (id: {self.id}, name: {self.name}>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location category")
        #: The plural verbose name of the model
        verbose_name_plural = _("location categories")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
