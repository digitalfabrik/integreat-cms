import string
import random

from django.db import models
from django.utils import timezone

from backend.settings import WEBAPP_URL

from ...constants import status


class AbstractBasePageTranslation(models.Model):
    """
    Data model representing a page or imprint page translation

    :param status: The status of the page translation (choices: :mod:`cms.constants.status`)
    :param title: The title of the page translation
    :param text: The content of the page translation
    :param currently_in_translation: Flag to indicate a translation is being updated by an external translator
    :param version: The revision number of the page translation
    :param minor_edit: Flag to indicate whether the difference to the previous revision requires an update in other
                       languages
    :param created_date: The date and time when the page translation was created
    :param last_updated: The date and time when the page translation was last updated

    Fields to be implemented in the inheriting model:

    :param permalink: The permalink to the page the translation
    :param page: The page the translation belongs to
    :param language: The :class:`~cms.models.languages.language.Language` of the page translation
    :param creator: The :class:`~django.contrib.auth.models.User` who created the page translation
    """

    title = models.CharField(max_length=250)
    text = models.TextField(blank=True)
    status = models.CharField(
        max_length=6, choices=status.CHOICES, default=status.DRAFT
    )
    currently_in_translation = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=0)
    minor_edit = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    short_url_id = models.CharField(max_length=10, default="")

    @property
    def page(self):
        """
        The page the translation belongs to
        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def language(self):
        """
        The language of the page translation
        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def creator(self):
        """
        The user who created the page translation
        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def permalink(self):
        """
        This property calculates the permalink dynamically
        To be implemented in the inheriting model

        :return: The permalink of the page
        :rtype: str
        """
        raise NotImplementedError

    @property
    def foreign_object(self):
        """
        This property is an alias of the page foreign key and is needed to generalize the :mod:`~cms.utils.slug_utils`
        for all content types

        :return: The page to which the translation belongs
        :rtype: ~cms.models.pages.page.Page
        """
        return self.page

    def get_absolute_url(self):
        """
        This helper function returns the absolute url to the webapp view of the page translation

        :return: The absolute url of a page translation
        :rtype: str
        """
        return "/" + self.permalink

    @property
    def short_url(self):
        """
        This function generates unique string and returns the short url to the page translation

        :return: The short url of a page translation
        :rtype: str
        """
        if not (self.short_url_id):
            chars = string.ascii_letters + string.digits
            self.short_url_id = "".join((random.choice(chars) for i in range(10)))
            self.save()
        return "s/" + self.short_url_id

    @property
    def available_languages(self):
        """
        This property checks in which :class:`~cms.models.languages.language.Language` the page is translated apart
        from ``self.language``.
        It only returns languages which have a public translation, so drafts are not included here.
        The returned dict has the following format::

            {
                available_translation.language.code: {
                    'id': available_translation.id,
                    'url': available_translation.permalink
                },
                ...
            }

        :return: A dictionary containing the available languages of a page translation
        :rtype: dict
        """
        languages = self.page.languages
        languages.remove(self.language)
        available_languages = {}
        for language in languages:
            other_translation = self.page.get_public_translation(language.code)
            if other_translation:
                available_languages[language.code] = {
                    "id": other_translation.id,
                    "url": other_translation.permalink,
                }
        return available_languages

    @property
    def sitemap_alternates(self):
        """
        This property returns the langauge alternatives of a page translation for the use in sitemaps.
        Similar to :func:`cms.models.pages.page_translation.PageTranslation.available_languages`, but in a slightly
        different format.

        :return: A list of dictionaries containing the alternative translations of a page translation
        :rtype: list [ dict ]
        """
        languages = self.page.languages
        languages.remove(self.language)
        available_languages = []
        for language in languages:
            other_translation = self.page.get_public_translation(language.code)
            if other_translation:
                available_languages.append(
                    {
                        "location": f"{WEBAPP_URL}{other_translation.get_absolute_url()}",
                        "lang_code": other_translation.language.code,
                    }
                )
        return available_languages

    @property
    def source_translation(self):
        """
        This property returns the translation which was used to create the ``self`` translation.
        It derives this information from the :class:`~cms.models.regions.region.Region`'s root
        :class:`~cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The page translation in the source :class:`~cms.models.languages.language.Language` (:obj:`None` if
                 the translation is in the :class:`~cms.models.regions.region.Region`'s default
                 :class:`~cms.models.languages.language.Language`)
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        source_language_tree_node = self.page.region.language_tree_nodes.get(
            language=self.language
        ).parent
        if source_language_tree_node:
            return self.page.get_translation(source_language_tree_node.code)
        return None

    @property
    def latest_public_revision(self):
        """
        This property is a link to the most recent public version of this translation.
        If the translation itself is not public, this property can return a revision which is older than ``self``.

        :return: The latest public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        """
        This property is a link to the most recent major version of this translation.

        :return: The latest major revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        """
        This property is a link to the most recent major public version of this translation.
        This is used when translations, which are derived from this translation, check whether they are up to date.

        :return: The latest major public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        """
        This property is a shortcut to the previous revision of this translation

        :return: The previous translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        version = self.version - 1
        return self.page.translations.filter(
            language=self.language,
            version=version,
        ).first()

    @property
    def is_outdated(self):
        """
        This property checks whether a translation is outdated and thus needs a new revision of the content.
        This happens, when the source translation is updated and the update is no `minor_edit`.

        * If the translation is currently being translated, it is considered not outdated.
        * If the translation's language is the region's default language, it is defined to be never outdated.
        * If the translation's source translation is already outdated, then the translation itself also is.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.

        Otherwise, the outdated flag is calculated by comparing the `last_updated`-field of the translation and its
        source translation.

        :return: Flag to indicate whether the translation is outdated
        :rtype: bool
        """
        # If the page translation is currently in translation, it is defined as not outdated
        if self.currently_in_translation:
            return False
        source_translation = self.source_translation
        # If self.language is the root language, this translation can never be outdated
        if not source_translation:
            return False
        # If the source translation is outdated, this translation can not be up to date
        if source_translation.is_outdated:
            return True
        self_revision = self.latest_major_public_revision
        source_revision = source_translation.latest_major_public_revision
        # If one of the translations has no major public revision, it cannot be outdated
        if not self_revision or not source_revision:
            return False
        return self_revision.last_updated < source_revision.last_updated

    @property
    def is_up_to_date(self):
        """
        This property checks whether a translation is up to date.
        A translation is considered up to date when it is not outdated and not being translated at the moment.

        :return: Flag which indicates whether a translation is up to date
        :rtype: bool
        """
        return not self.currently_in_translation and not self.is_outdated

    class Meta:
        abstract = True
