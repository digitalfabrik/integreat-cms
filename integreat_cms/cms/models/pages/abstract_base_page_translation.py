from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Literal

    from .abstract_base_page import AbstractBasePage

from ..abstract_content_translation import AbstractContentTranslation


class AbstractBasePageTranslation(AbstractContentTranslation):
    """
    Data model representing a page or imprint page translation
    """

    @cached_property
    def page(self) -> AbstractBasePage:
        """
        The page the translation belongs to

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @cached_property
    def short_url(self) -> str:
        """
        This property calculates the short url dynamically

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @staticmethod
    def foreign_field() -> Literal["page"]:
        """
        Returns the string "page" which ist the field name of the reference to the page which the translation belongs to

        :return: The foreign field name
        """
        return "page"

    @cached_property
    def foreign_object(self) -> AbstractBasePage:
        """
        This property is an alias of the page foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The page to which the translation belongs
        """
        return self.page

    @cached_property
    def readable_title(self) -> str:
        """
        Get the title of a page translation including the title in the best translation

        :return: The readable title of the page translation
        """
        # Build readable page translation title
        best_translation = self.page.best_translation
        best_translation_title = (
            f' {best_translation.language}: "{best_translation.title}"'
        )
        # Check whether page translation has title
        if self.title:
            # Start with translation title if exists
            readable_title = f'"{self.title}"'
            if (
                best_translation.title != self.title
                and best_translation.language != self.language
            ):
                readable_title += " (" + _("Title in") + best_translation_title + ")"
        else:
            # Start directly with the title of the best translation
            readable_title = _("with the title in") + best_translation_title
        return readable_title

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("page translations")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page", "-version"]
        #: The default permissions for this model
        default_permissions = ()
        #: This model is an abstract base class
        abstract = True
