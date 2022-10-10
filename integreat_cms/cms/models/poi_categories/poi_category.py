from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel


class POICategory(AbstractBaseModel):
    """
    Data model representing a POI category.
    """

    @cached_property
    def name(self):
        """
        This function returns the name of the category in the "best" translation

        :return: The name of the category
        :rtype: str
        """
        return (
            self.best_translation.name
            if self.best_translation
            else str(_("POI category"))
        )

    def get_translation(self, language_slug):
        """
        Get the translation of this category in a given language

        :param language_slug: language in which the poi category is to be shown
        :type language_slug: Language

        :return: translation of the poi category in the language
                 if no translation is saved for the language, the category name of the POICategory
        :rtype: ~integreat_cms.cms.models.poi_categories.poi_category_translation.POICategoryTranslation
        """
        return self.translations.filter(language__slug=language_slug).first()

    @cached_property
    def backend_translation(self):
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        :rtype: ~integreat_cms.cms.models.poi_categories.poi_category_translation.POICategoryTranslation
        """
        return self.get_translation(get_language())

    @cached_property
    def best_translation(self):
        """
        This function returns the translation of this category in the current backend language and if it doesn't
        exist, it provides a fallback to the first translation.

        :return: The "best" translation of this category for displaying in the backend
        :rtype: ~integreat_cms.cms.models.poi_categories.poi_category_translation.POICategoryTranslation
        """
        return self.backend_translation or self.translations.first()

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``POICategory object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the category
        :rtype: str
        """
        return self.name

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<POI Category: POICategory object (id, category name)>``.
        It is used for logging.

        :return: The canonical string representation of the category
        :rtype: str
        """
        return f"<POI Category (id: {self.id}, name: {self.name}>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("location category")
        #: The plural verbose name of the model
        verbose_name_plural = _("location categories")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
