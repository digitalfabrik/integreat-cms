from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils import timezone

from ...constants import status


class AbstractBasePage(models.Model):
    """
    Abstract base class for page and imprint page models.
    """

    explicitly_archived = models.BooleanField(
        default=False,
        verbose_name=_("explicitly archived"),
        help_text=_("Whether or not the page is explicitly archived"),
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )
    last_updated = models.DateTimeField(
        auto_now=True, verbose_name=_("modification date")
    )

    @property
    def archived(self):
        """
        This is an alias of ``explicitly_archived``. Used for hierarchical pages to implement a more complex notion of
        explicitly and implicitly archived pages (see :func:`~cms.models.pages.page.Page.archived`).

        :return: Whether or not this page is archived
        :rtype: bool
        """
        return self.explicitly_archived

    @property
    def region(self):
        """
        The region to which the page belongs (related name: ``pages``)
        To be implemented in the inheriting model.
        """
        raise NotImplementedError

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~cms.models.languages.language.Language` objects, to which a page
        translation exists.

        :return: list of all :class:`~cms.models.languages.language.Language` a page is translated into
        :rtype: list [ ~cms.models.languages.language.Language ]
        """
        page_translations = self.translations.prefetch_related("language").all()
        languages = []
        for page_translation in page_translations:
            if page_translation.language not in languages:
                languages.append(page_translation.language)
        return languages

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The page translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(language__slug=language_slug).first()

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of a page.

        :param language_slug: The slug of the requested :class:`~cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a page
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(
            language__slug=language_slug,
            status=status.PUBLIC,
        ).first()

    @property
    def backend_translation(self):
        """
        This function returns the translation of this page in the current backend language.

        :return: The backend translation of a page
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_translation(self):
        """
        This function returns the translation of this page in the region's default language.
        Since a page can only be created by creating a translation in the default language, this is guaranteed to return
        a page translation.

        :return: The default translation of a page
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @property
    def best_translation(self):
        """
        This function returns the translation of this page in the current backend language and if it doesn't exist, it
        provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a page for displaying in the backend
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.backend_translation or self.default_translation

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Page object at 0xDEADBEEF>

        :return: The string representation of the page with information about the most important fields (useful for
                 debugging purposes)
        :rtype: str
        """
        if self.id:
            first_translation = self.get_first_translation()
            if first_translation:
                return f"(id: {self.id}, slug: {first_translation.slug} ({first_translation.language.slug}))"
            return f"(id: {self.id})"
        return super().__str__()

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page")
        #: The plural verbose name of the model
        verbose_name_plural = _("pages")
        #: This model is an abstract base class
        abstract = True
