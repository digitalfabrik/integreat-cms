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
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AbstractBasePage object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the page
        :rtype: str
        """
        return self.best_translation.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractBasePage: AbstractBasePage object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the page
        :rtype: str
        """
        class_name = type(self).__name__
        return f"<{class_name} (id: {self.id}, region: {self.region.slug}, slug: {self.best_translation.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page")
        #: The plural verbose name of the model
        verbose_name_plural = _("pages")
        #: This model is an abstract base class
        abstract = True
