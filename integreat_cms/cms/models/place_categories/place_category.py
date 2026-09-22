from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from .place_category_translation import PlaceCategoryTranslation

from ...constants import placecategory
from ..abstract_base_model import AbstractBaseModel


class PlaceCategory(AbstractBaseModel):
    """
    Data model representing a Place category.
    """

    icon = models.CharField(
        choices=placecategory.ICONS,
        max_length=256,
        verbose_name=_("icon"),
        blank=True,
        null=True,
        help_text=_("Select an icon for this category"),
    )

    color = models.CharField(
        choices=placecategory.COLORS,
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
            else str(_("Place category"))
        )

    @cached_property
    def prefetched_translations_by_language_slug(
        self,
    ) -> dict[str, PlaceCategoryTranslation]:
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return {
            translation.language.slug: translation
            for translation in self.translations.all()
        }

    def get_translation(self, language_slug: str) -> PlaceCategoryTranslation | None:
        """
        Get the translation of this category in a given language

        :param language_slug: language in which the place category is to be shown
        :return: translation of the place category in the language
                 if no translation is saved for the language, the category name of the PlaceCategory
        """
        return self.prefetched_translations_by_language_slug.get(language_slug)

    @cached_property
    def backend_translation(self) -> PlaceCategoryTranslation | None:
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        """
        return self.get_translation(get_language())

    @cached_property
    def best_translation(self) -> PlaceCategoryTranslation:
        """
        This function returns the translation of this category in the current backend language and if it doesn't
        exist, it provides a fallback to the first translation.

        :return: The "best" translation of this category for displaying in the backend
        """
        return self.backend_translation or self.translations.first()

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``PlaceCategory object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the category
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Place Category: PlaceCategory object (id, category name)>``.
        It is used for logging.

        :return: The canonical string representation of the category
        """
        class_name = type(self).__name__
        if not self.pk:
            return f"<{class_name} (unsaved instance)>"
        return f"<Place Category (id: {self.id}, name: {self.name}>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("place category")
        #: The plural verbose name of the model
        verbose_name_plural = _("place categories")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
