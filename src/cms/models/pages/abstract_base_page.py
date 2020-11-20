from django.db import models
from django.utils.translation import get_language
from django.utils import timezone

from ...constants import status


class AbstractBasePage(models.Model):
    """
    Abstract base class for page and imprint page models.

    :param explicitly_archived: Whether or not the page is explicitly archived
    :param created_date: The date and time when the page was created
    :param last_updated: The date and time when the page was last updated

    Fields to be implemented in the inheriting model:

    :param icon: The title image of the page
    :param region: The :class:`~cms.models.regions.region.Region` to which the page belongs
    """

    explicitly_archived = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

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
    def icon(self):
        """
        The title image of the page
        To be implemented in the inheriting model.
        """
        raise NotImplementedError

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

    def get_translation(self, language_code):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~cms.models.languages.language.Language` code.

        :param language_code: The code of the desired :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The page translation in the requested :class:`~cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(language__code=language_code).first()

    def get_first_translation(self, priority_language_codes=None):
        """
        Helper function for page labels, second level paths etc. where the ancestor translation might not exist
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the first requested :class:`~cms.models.languages.language.Language` code that matches.
        So a lower list index means a higher priority.

        :param priority_language_codes: A list of :class:`~cms.models.languages.language.Language` codes,
                                        defaults to ``None``
        :type priority_language_codes: list [ str ], optional

        :return: The first page translation which matches one of the :class:`~cms.models.languages.language.Language`
                 given or :obj:`None` if no translation exists
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        # Taking [] directly as default parameter would be dangerous because it is mutable
        if not priority_language_codes:
            priority_language_codes = []
        for language_code in priority_language_codes + ["en-us", "de-de"]:
            if self.translations.filter(language__code=language_code).exists():
                return self.translations.filter(language__code=language_code).first()
        return self.translations.first()

    def get_public_translation(self, language_code):
        """
        This function retrieves the newest public translation of a page.

        :param language_code: The code of the requested :class:`~cms.models.languages.language.Language`
        :type language_code: str

        :return: The public translation of a page
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.translations.filter(
            language__code=language_code,
            status=status.PUBLIC,
        ).first()

    def best_language_title(self):
        """
        This function tries to determine which title to be used for a page. The first priority is the current backend
        language. If no translation is present in this language, the fallback is the region's default language.

        :return: The "best" title for showing pages in the backend
        :rtype: str
        """
        page_translation = self.translations.filter(language__code=get_language())
        if not page_translation:
            alt_code = self.region.default_language.code
            page_translation = self.translations.filter(language__code=alt_code)
        return page_translation.first().title

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
                return f"(id: {self.id}, slug: {first_translation.slug} ({first_translation.language.code}))"
            return f"(id: {self.id})"
        return super().__str__()

    class Meta:
        abstract = True
