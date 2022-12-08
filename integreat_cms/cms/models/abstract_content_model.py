import logging

from copy import deepcopy

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _
from django.utils import timezone

from ..constants import status, translation_status
from ..utils.content_edit_lock import get_locking_user
from .regions.region import Region
from .abstract_base_model import AbstractBaseModel

logger = logging.getLogger(__name__)


class ContentQuerySet(models.QuerySet):
    """
    This queryset provides the option to prefetch translations for content objects
    """

    def prefetch_translations(self, to_attr="prefetched_translations", **filters):
        r"""
        Get the queryset including the custom attribute ``to_attr`` which contains the latest
        translations of each content object in each language, optionally filtered by the given ``status``

        :param to_attr: To which attribute the prefetched translations should be added [optional, defaults to ``prefetched_translations``]
        :type to_attr: str

        :param \**filters: Additional filters to be applied on the translations (e.g. by status)
        :type \**filters: dict

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.filter(**filters)
                .order_by(foreign_field, "language_id", "-version")
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr=to_attr,
            )
        )

    def prefetch_public_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_public_translations`` which contains the latest
        public translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        return self.prefetch_translations(
            to_attr="prefetched_public_translations", status=status.PUBLIC
        )

    def prefetch_public_or_draft_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_public_or_draft_translations`` which contains the latest
        public or draft translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        return self.prefetch_translations(
            to_attr="prefetched_public_or_draft_translations",
            status__in=[status.DRAFT, status.PUBLIC],
        )

    def prefetch_major_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_major_translations`` which contains the
        latest major (in other words not a minor edit) translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        return self.prefetch_translations(
            to_attr="prefetched_major_translations",
            minor_edit=False,
        )

    def prefetch_major_public_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_major_public_translations`` which contains the
        latest major (in other words not a minor edit) public translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        return self.prefetch_translations(
            to_attr="prefetched_major_public_translations",
            status=status.PUBLIC,
            minor_edit=False,
        )


# pylint: disable=too-many-public-methods
class AbstractContentModel(AbstractBaseModel):
    """
    Abstract base class for all content models
    """

    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, verbose_name=_("region")
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )

    #: Custom model manager for content objects
    objects = ContentQuerySet.as_manager()

    #: Whether translations should be returned in the default language if they do not exist
    fallback_translations_enabled = False

    @cached_property
    def languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a translation exists.

        :return: The existing languages of this content object
        :rtype: list
        """
        translations = self.prefetched_translations_by_language_slug.values()
        return [translation.language for translation in translations]

    def available_translations(self):
        """
        This method returns an iterator over all available translations, respecting the `fallback_translations_enabled` setting.

        :return: An iterator over all translations
        :rtype: Iterator[:class:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation`]
        """
        # Check if fallback translation should be used
        if self.fallback_translations_enabled:
            all_languages = self.region.visible_languages
        else:
            all_languages = self.public_languages

        for language in all_languages:
            public_translation = self.get_public_translation(language.slug)
            if public_translation:
                yield public_translation

    @cached_property
    def public_languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a public translation exists and which are visible in this region.

        :return: The existing languages of this content object
        :rtype: list
        """
        translations = self.prefetched_public_translations_by_language_slug.values()
        return [
            translation.language
            for translation in translations
            if translation.language in self.region.visible_languages
        ]

    def get_prefetched_translations_by_language_slug(
        self, attr="prefetched_translations", **filters
    ):
        r"""
        This method returns a mapping from language slugs to their latest translations of this object

        :param attr: Which attribute should be tried to get the prefetched translations [optional, defaults to ``"prefetched_translations"``]
        :type attr: str

        :param \**filters: Additional filters to be applied on the translations (e.g. by status)
        :type \**filters: dict

        :return: The prefetched translations by language slug
        :rtype: dict
        """
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            prefetched_translations = getattr(self, attr)
        except AttributeError:
            # If the translations were not prefetched, query it from the database
            prefetched_translations = (
                self.translations.filter(**filters)
                .select_related("language")
                .order_by("language__id", "-version")
                .distinct("language__id")
                .all()
            )
        return {
            translation.language.slug: translation
            for translation in prefetched_translations
        }

    @cached_property
    def prefetched_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their latest translations of this object

        :return: The prefetched translations by language slug
        :rtype: dict
        """
        return self.get_prefetched_translations_by_language_slug()

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~integreat_cms.cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.prefetched_translations_by_language_slug.get(language_slug)

    @cached_property
    def prefetched_public_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: dict
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_public_translations", status=status.PUBLIC
        )

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        public_translation = self.prefetched_public_translations_by_language_slug.get(
            language_slug
        )
        # Check if fallback translation should be used
        if not public_translation and self.fallback_translations_enabled:
            # Get the fallback translation
            public_translation = (
                self.prefetched_public_translations_by_language_slug.get(
                    self.region.default_language.slug
                )
            )
            if public_translation:
                # Create copy in memory to make sure original translation is not affected by changes
                public_translation = deepcopy(public_translation)
                # Reset id to make sure id does not conflict with existing translation
                public_translation.id = None
                # Fake the requested language
                public_translation.language = self.region.language_node_by_slug[
                    language_slug
                ].language
                # Reset prefetched translations
                public_translation.foreign_object.prefetched_public_translations_by_language_slug = (
                    self.prefetched_public_translations_by_language_slug
                )
                # Clear cached property in case url with different language was already calculated before
                try:
                    del public_translation.url_prefix
                except AttributeError:
                    pass
        return public_translation

    @cached_property
    def prefetched_public_or_draft_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: dict
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_public_or_draft_translations",
            status__in=[status.DRAFT, status.PUBLIC],
        )

    def get_public_or_draft_translation(self, language_slug):
        """
        This function retrieves the newest public or draft translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.prefetched_public_or_draft_translations_by_language_slug.get(
            language_slug
        )

    @cached_property
    def prefetched_major_public_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their major public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: dict
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_major_public_translations",
            status=status.PUBLIC,
            minor_edit=False,
        )

    def get_major_public_translation(self, language_slug):
        """
        This function retrieves the newest major public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.prefetched_major_public_translations_by_language_slug.get(
            language_slug
        )

    @cached_property
    def prefetched_major_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their major translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: dict
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_major_translations",
            minor_edit=False,
        )

    def get_major_translation(self, language_slug):
        """
        This function retrieves the newest major translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.prefetched_major_translations_by_language_slug.get(language_slug)

    @cached_property
    def backend_translation(self):
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.get_translation(get_language())

    @cached_property
    def default_translation(self):
        """
        This function returns the translation of this content object in the region's default language.
        Since a content object can only be created by creating a translation in the default language, this is guaranteed
        to return a object translation (Exception: When the default language tree node is changed to another language
        after the page has been created, the default translation might not exist).

        :return: The default translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.get_translation(self.region.default_language.slug)

    @cached_property
    def best_translation(self):
        """
        This function returns the translation of this content object in the current backend language and if it doesn't
        exist, it provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a content object for displaying in the backend
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return (
            self.backend_translation
            or self.default_translation
            or self.translations.first()
        )

    def get_translation_state(self, language_slug):
        """
        This function returns the current state of a translation in the given language.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: A string describing the state of the translation, one of :data:`~integreat_cms.cms.constants.translation_status.CHOICES`
        :rtype: str
        """
        translation = self.get_translation(language_slug)
        if not translation:
            if self.fallback_translations_enabled:
                fallback_translation = self.get_translation(
                    self.region.default_language.slug
                )
                if fallback_translation:
                    return translation_status.FALLBACK
            return translation_status.MISSING
        return translation.translation_state

    @cached_property
    def translation_states(self):
        """
        This property calculates all translations states of the object

        :return: A dictionary containing each language as key and the given translation state as value
        :rtype: dict
        """
        return {
            node.slug: (node.language, self.get_translation_state(node.slug))
            for node in self.region.language_tree
            if node.active
        }

    @property
    def edit_lock_key(self):
        """
        This property returns the key that is used to lock this specific content object

        :return: A tuple of the id of this object and the classname
        :rtype: tuple
        """
        return (self.id, type(self).__name__)

    def get_locking_user(self):
        """
        This method returns the user that is currently locking this content object.

        :return: The user
        :rtype: ~django.contrib.auth.models.User
        """
        return get_locking_user(*self.edit_lock_key)

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AbstractContentModel object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the content object
        :rtype: str
        """
        return self.best_translation.title

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractContentModel: AbstractContentModel object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the content object
        :rtype: str
        """
        class_name = type(self).__name__
        return f"<{class_name} (id: {self.id}, region: {self.region.slug}, slug: {self.best_translation.slug})>"

    class Meta:
        #: This model is an abstract base class
        abstract = True
