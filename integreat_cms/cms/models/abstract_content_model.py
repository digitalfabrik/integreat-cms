import logging

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import get_language, ugettext_lazy as _
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

    def prefetch_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_translations`` which contains the latest
        translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.order_by(
                    foreign_field, "language_id", "-version"
                )
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr="prefetched_translations",
            )
        )

    def prefetch_public_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_public_translations`` which contains the latest
        public translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.filter(status=status.PUBLIC)
                .order_by(foreign_field, "language_id", "-version")
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr="prefetched_public_translations",
            )
        )

    def prefetch_major_public_translations(self):
        """
        Get the queryset including the custom attribute ``prefetched_major_public_translations`` which contains the
        latest major (in other words not a minor edit) public translations of each content object in each language

        :return: The queryset of content objects
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel ]
        """
        TranslationModel = self.model.get_translation_model()
        foreign_field = TranslationModel.foreign_field() + "_id"
        return self.prefetch_related(
            models.Prefetch(
                "translations",
                queryset=TranslationModel.objects.filter(
                    status=status.PUBLIC,
                    minor_edit=False,
                )
                .order_by(foreign_field, "language_id", "-version")
                .distinct(foreign_field, "language_id")
                .select_related("language"),
                to_attr="prefetched_major_public_translations",
            )
        )


class AbstractContentModel(AbstractBaseModel):
    """
    Abstract base class for all content models
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        verbose_name=_("region"),
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )

    #: Custom model manager for content objects
    objects = ContentQuerySet.as_manager()

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

    @cached_property
    def public_languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a translation exists.

        :return: The existing languages of this content object
        :rtype: list
        """
        translations = self.prefetched_public_translations_by_language_slug.values()
        return [translation.language for translation in translations]

    @cached_property
    def prefetched_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their latest translations of this object

        :return: The prefetched translations by language slug
        :rtype: dict
        """
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            prefetched_translations = self.prefetched_translations
        except AttributeError:
            # If the translations were not prefetched, query it from the database
            prefetched_translations = (
                self.translations.select_related("language")
                .order_by("language__id", "-version")
                .distinct("language__id")
                .all()
            )
        return {
            translation.language.slug: translation
            for translation in prefetched_translations
        }

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
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            prefetched_public_translations = self.prefetched_public_translations
        except AttributeError:
            # If the translations were not prefetched, query it from the database
            prefetched_public_translations = (
                self.translations.filter(status=status.PUBLIC)
                .select_related("language")
                .order_by("language__id", "-version")
                .distinct("language__id")
            )
        return {
            translation.language.slug: translation
            for translation in prefetched_public_translations
        }

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of a content object
        :rtype: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
        """
        return self.prefetched_public_translations_by_language_slug.get(language_slug)

    @cached_property
    def prefetched_major_public_translations_by_language_slug(self):
        """
        This method returns a mapping from language slugs to their major public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        :rtype: dict
        """
        try:
            # Try to get the prefetched translations (which are already distinct per language)
            prefetched_public_translations = self.prefetched_major_public_translations
        except AttributeError:
            # If the translations were not prefetched, query it from the database
            prefetched_public_translations = (
                self.translations.filter(status=status.PUBLIC, minor_edit=False)
                .select_related("language")
                .order_by("language__id", "-version")
                .distinct("language__id")
            )
        return {
            translation.language.slug: translation
            for translation in prefetched_public_translations
        }

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
        translation = self.get_major_public_translation(language_slug)
        if not translation:
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
