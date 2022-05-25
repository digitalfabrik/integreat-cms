from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .languages.language import Language
from .abstract_base_model import AbstractBaseModel
from ..constants import status, translation_status
from ..utils.translation_utils import ugettext_many_lazy as __


# pylint: disable=too-many-public-methods
class AbstractContentTranslation(AbstractBaseModel):
    """
    Data model representing a translation of some kind of content (e.g. pages or events)
    """

    title = models.CharField(max_length=1024, verbose_name=_("title"))
    slug = models.SlugField(
        max_length=1024,
        allow_unicode=True,
        verbose_name=_("link"),
        help_text=__(
            _("String identifier without spaces and special characters."),
            _("Unique per region and language."),
            _("Leave blank to generate unique parameter from title."),
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.status`
    status = models.CharField(
        max_length=9,
        choices=status.CHOICES,
        default=status.DRAFT,
        verbose_name=_("status"),
    )
    content = models.TextField(blank=True, verbose_name=_("content"))
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        verbose_name=_("language"),
    )
    currently_in_translation = models.BooleanField(
        default=False,
        verbose_name=_("currently in translation"),
        help_text=_(
            "Flag to indicate a translation is being updated by an external translator"
        ),
    )
    version = models.PositiveIntegerField(default=0, verbose_name=_("revision"))
    minor_edit = models.BooleanField(
        default=False,
        verbose_name=_("minor edit"),
        help_text=_(
            "Tick if this change does not require an update of translations in other languages."
        ),
    )
    last_updated = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("modification date"),
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("creator"),
    )

    @staticmethod
    def foreign_field():
        """
        The field name of the reference to the foreign object which the translation belongs to

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @cached_property
    def foreign_object(self):
        """
        Returns the object the translation belongs to
        This is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils` for all content types

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @cached_property
    def url_prefix(self):
        """
        Generates the prefix of the url of the content translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The prefix to the url
        :rtype: str
        """
        return (
            "/"
            + "/".join(
                filter(
                    None,
                    [
                        self.foreign_object.region.slug,
                        self.language.slug,
                        self.url_infix,
                    ],
                )
            )
            + "/"
        )

    @cached_property
    def url_infix(self):
        """
        Generates the infix of the url of the content translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @cached_property
    def base_link(self):
        """
        Generates the base link which is the whole url without slug

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: the base link of the content
        :rtype: str
        """
        if not self.id:
            return settings.WEBAPP_URL + "/"
        return settings.WEBAPP_URL + self.url_prefix

    def get_absolute_url(self):
        """
        Generates the absolute url of the content translation object

        Here is an example for demonstrating the components of a page url::

            https://integreat.app/augsburg/en/welcome/city-map/attractions/
            |-------------------------------------------------------------|    full_url
                                 |----------------------------------------|    get_absolute_url()
            |-------------------------------------------------|                base_link
                                 |----------------------------|                url_prefix
                                             |----------------|                url_infix
                                                              |-----------|    slug

        Here is an example for demonstrating the components of an event url::

            https://integreat.app/augsburg/en/events/test-event/
            |--------------------------------------------------|    full_url
                                 |-----------------------------|    get_absolute_url()
            |---------------------------------------|               base_link
                                 |------------------|               url_prefix
                                             |------|               url_infix
                                                    |----------|    slug

        :return: The absolute url
        :rtype: str
        """
        return self.url_prefix + self.slug + "/"

    @cached_property
    def full_url(self):
        """
        This property returns the full url of this content translation object

        :return: The full url
        :rtype: str
        """
        return settings.WEBAPP_URL + self.get_absolute_url()

    @cached_property
    def backend_edit_link(self):
        """
        Generates the url of the edit page for the content

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @cached_property
    def available_languages(self):
        """
        This property checks in which :class:`~integreat_cms.cms.models.languages.language.Language` the content is
        translated apart from ``self.language``
        It only returns languages which have a public translation, so drafts are not included here.
        The returned dict has the following format::

            {
                available_translation.language.slug: {
                    'id': available_translation.id,
                    'url': available_translation.permalink
                    'path': available_translation.path
                },
                ...
            }

        :return: A dictionary containing the available languages of a content translation
        :rtype: dict
        """
        available_languages = {}
        # Check if fallback translation should be used
        if self.foreign_object.fallback_translations_enabled:
            all_languages = self.foreign_object.region.active_languages
        else:
            all_languages = self.foreign_object.public_languages
        for language in all_languages:
            if language == self.language:
                continue
            public_translation = self.foreign_object.get_public_translation(
                language.slug
            )
            if public_translation:
                absolute_url = public_translation.get_absolute_url()
                available_languages[language.slug] = {
                    "id": public_translation.id,
                    "url": settings.BASE_URL + absolute_url,
                    "path": absolute_url,
                }
        return available_languages

    @cached_property
    def sitemap_alternates(self):
        """
        This property returns the language alternatives of a content translation for the use in sitemaps.
        Similar to :func:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.available_languages`,
        but in a slightly different format.

        :return: A list of dictionaries containing the alternative translations of a content translation
        :rtype: list [ dict ]
        """
        available_languages = []
        for language in self.foreign_object.public_languages:
            if language == self.language:
                continue
            other_translation = self.foreign_object.get_public_translation(
                language.slug
            )
            if other_translation:
                available_languages.append(
                    {
                        "location": f"{settings.WEBAPP_URL}{other_translation.get_absolute_url()}",
                        "lang_slug": other_translation.language.slug,
                    }
                )
        return available_languages

    @cached_property
    def source_language(self):
        """
        This property returns the source language of this language in this
        :class:`~integreat_cms.cms.models.regions.region.Region`'s language tree

        :return: The source language of this translation
        :rtype: ~integreat_cms.cms.models.languages.language.Language
        """
        return self.foreign_object.region.get_source_language(self.language.slug)

    @cached_property
    def source_translation(self):
        """
        This property returns the translation which was used to create the ``self`` translation.
        It derives this information from the :class:`~integreat_cms.cms.models.regions.region.Region`'s root
        :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The content translation in the source :class:`~integreat_cms.cms.models.languages.language.Language`
                 (:obj:`None` if the translation is in the :class:`~integreat_cms.cms.models.regions.region.Region`'s
                 default :class:`~integreat_cms.cms.models.languages.language.Language`)
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        if self.source_language:
            return self.foreign_object.get_translation(self.source_language.slug)
        return None

    @cached_property
    def public_source_translation(self):
        """
        This property returns the public translation which was used to create the ``self`` translation.
        It derives this information from the :class:`~integreat_cms.cms.models.regions.region.Region`'s root
        :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The content translation in the source :class:`~integreat_cms.cms.models.languages.language.Language`
                 (:obj:`None` if no public source translation exists)
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        if self.source_language:
            return self.foreign_object.get_public_translation(self.source_language.slug)
        return None

    @cached_property
    def major_public_source_translation(self):
        """
        This property returns the latest major public version of the translation which was used to create the ``self``
        translation. It derives this information from the :class:`~integreat_cms.cms.models.regions.region.Region`'s root
        :class:`~integreat_cms.cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The content translation in the source :class:`~integreat_cms.cms.models.languages.language.Language`
                 (:obj:`None` if the translation is in the :class:`~integreat_cms.cms.models.regions.region.Region`'s
                 default :class:`~integreat_cms.cms.models.languages.language.Language`)
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        if self.source_language:
            return self.foreign_object.get_major_public_translation(
                self.source_language.slug
            )
        return None

    @cached_property
    def latest_version(self):
        """
        This property is a link to the most recent version of this translation.

        :return: The latest revision of the translation
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.foreign_object.get_translation(self.language.slug)

    @cached_property
    def public_version(self):
        """
        This property is a link to the most recent public version of this translation.
        If the translation itself is not public, this property can return a revision which is older than ``self``.

        :return: The latest public revision of the translation
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.foreign_object.get_public_translation(self.language.slug)

    @cached_property
    def major_public_version(self):
        """
        This property is a link to the most recent major public version of this translation.
        This is used when translations, which are derived from this translation, check whether they are up to date.

        :return: The latest major public revision of the translation
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.foreign_object.get_major_public_translation(self.language.slug)

    @cached_property
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
        return self.translation_state == translation_status.OUTDATED

    @cached_property
    def is_up_to_date(self):
        """
        This property checks whether a translation is up to date.
        A translation is considered up to date when it is not outdated and not being translated at the moment.

        :return: Flag which indicates whether a translation is up to date
        :rtype: bool
        """
        return self.translation_state == translation_status.UP_TO_DATE

    # pylint: disable=too-many-return-statements
    @cached_property
    def translation_state(self):
        """
        This function returns the current state of a translation in the given language.

        :return: A string describing the state of the translation, one of :data:`~integreat_cms.cms.constants.translation_status.CHOICES`
        :rtype: str
        """
        translation = self.major_public_version
        if not translation:
            # If the page does not have a major public version, it is considered "missing" (keep in mind that it might
            # have draft versions or public versions that are marked as "minor edit")
            return translation_status.MISSING
        if translation.currently_in_translation:
            return translation_status.IN_TRANSLATION
        if not self.source_language:
            # If the language of this translation is the root of this region's language tree, it is always "up to date"
            return translation_status.UP_TO_DATE
        source_translation = self.major_public_source_translation
        if not source_translation:
            # If the source language does not have a major public version, the translation is considered "outdated",
            # because the content is not in sync with its source translation
            return translation_status.OUTDATED
        if source_translation.translation_state == translation_status.OUTDATED:
            # If the source translation is already outdated, this translation is as well
            return translation_status.OUTDATED
        if translation.last_updated > source_translation.last_updated:
            # If the translation was edited after the source translation, we consider it up to date
            return translation_status.UP_TO_DATE
        # If the translation was edited before the last major change in the source language, it is outdated
        return translation_status.OUTDATED

    @classmethod
    def search(cls, region, language_slug, query):
        """
        Searches for all content translations which match the given `query` in their title or slug.
        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region
        :param language_slug: The language slug
        :type language_slug: str
        :param query: The query string used for filtering the content translations
        :type query: str
        :return: A query for all matching objects
        :rtype: ~django.db.models.QuerySet
        """
        return (
            cls.objects.filter(
                **{cls.foreign_field() + "__region": region},
                language__slug=language_slug,
            )
            .filter(Q(slug__icontains=query) | Q(title__icontains=query))
            .distinct(cls.foreign_field())
        )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the content translation
        :rtype: str
        """
        return self.title

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method.
        It is used for logging.

        :return: The canonical string representation of the content translation
        :rtype: str
        """
        return (
            f"<{type(self).__name__} ("
            f"id: {self.id}, "
            f"{self.foreign_field()}_id: {self.foreign_object.id}, "
            f"language: {self.language.slug}, "
            f"slug: {self.slug})>"
        )

    def save(self, *args, **kwargs):
        r"""
        This overwrites the default Django :meth:`~django.db.models.Model.save` method,
        to update the last_updated field on changes.

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied kwargs
        :type \**kwargs: dict
        """
        if kwargs.pop("update_timestamp", True):
            self.last_updated = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        #: This model is an abstract base class
        abstract = True
