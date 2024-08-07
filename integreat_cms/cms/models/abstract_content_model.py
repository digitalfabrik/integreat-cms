from __future__ import annotations

import logging
from copy import copy
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any, Iterator

    from .abstract_content_translation import AbstractContentTranslation
    from .languages.language import Language

from ..constants import status, translation_status
from ..utils.content_edit_lock import get_locking_user
from .abstract_base_model import AbstractBaseModel
from .regions.region import Region

logger = logging.getLogger(__name__)


class ContentQuerySet(models.QuerySet):
    """
    This queryset provides the option to prefetch translations for content objects
    """

    def prefetch_translations(
        self, to_attr: str = "prefetched_translations", **filters: Any
    ) -> ContentQuerySet:
        r"""
        Get the queryset including the custom attribute ``to_attr`` which contains the latest
        translations of each content object in each language, optionally filtered by the given ``status``

        :param to_attr: To which attribute the prefetched translations should be added [optional, defaults to ``prefetched_translations``]
        :param \**filters: Additional filters to be applied on the translations (e.g. by status)
        :return: The queryset of content objects
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

    def prefetch_public_translations(
        self,
    ) -> ContentQuerySet:
        """
        Get the queryset including the custom attribute ``prefetched_public_translations`` which contains the latest
        public translations of each content object in each language

        :return: The queryset of content objects
        """
        return self.prefetch_translations(
            to_attr="prefetched_public_translations", status=status.PUBLIC
        )

    def prefetch_public_or_draft_translations(
        self,
    ) -> ContentQuerySet:
        """
        Get the queryset including the custom attribute ``prefetched_public_or_draft_translations`` which contains the latest
        public or draft translations of each content object in each language

        :return: The queryset of content objects
        """
        return self.prefetch_translations(
            to_attr="prefetched_public_or_draft_translations",
            status__in=[status.DRAFT, status.PUBLIC],
        )

    def prefetch_major_translations(self) -> ContentQuerySet:
        """
        Get the queryset including the custom attribute ``prefetched_major_translations`` which contains the
        latest major (in other words not a minor edit) translations of each content object in each language

        :return: The queryset of content objects
        """
        return self.prefetch_translations(
            to_attr="prefetched_major_translations",
            minor_edit=False,
        )

    def prefetch_major_public_translations(
        self,
    ) -> ContentQuerySet:
        """
        Get the queryset including the custom attribute ``prefetched_major_public_translations`` which contains the
        latest major (in other words not a minor edit) public translations of each content object in each language

        :return: The queryset of content objects
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

    #: Whether the HIX value is ignored (this is ``False`` by default if not overwritten by a submodel)
    hix_ignore: bool = False

    @property
    def fallback_translations_enabled(self) -> bool:
        """
        Whether translations should be returned in the default language if they do not exist

        :return: Whether fallback translations are enabled
        """
        return False

    @cached_property
    def languages(self) -> list[Language]:
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a translation exists.

        :return: The existing languages of this content object
        """
        translations = self.prefetched_translations_by_language_slug.values()
        return [translation.language for translation in translations]

    def available_translations(self) -> Iterator[Any]:
        """
        This method returns an iterator over all available translations, respecting the `fallback_translations_enabled` setting.

        :return: An iterator over all translations
        """
        # Check if fallback translation should be used
        all_languages = (
            self.region.visible_languages
            if self.fallback_translations_enabled
            else self.public_languages
        )

        for language in all_languages:
            if public_translation := self.get_public_translation(language.slug):
                yield public_translation

    @cached_property
    def public_languages(self) -> list[Language]:
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which a public translation exists and which are visible in this region.

        :return: The existing languages of this content object
        """
        translations = self.prefetched_public_translations_by_language_slug.values()
        return [
            translation.language
            for translation in translations
            if translation.language in self.region.visible_languages
        ]

    def get_prefetched_translations_by_language_slug(
        self, attr: str = "prefetched_translations", **filters: Any
    ) -> dict[str, AbstractContentTranslation]:
        r"""
        This method returns a mapping from language slugs to their latest translations of this object

        :param attr: Which attribute should be tried to get the prefetched translations [optional, defaults to ``"prefetched_translations"``]
        :param \**filters: Additional filters to be applied on the translations (e.g. by status)
        :return: The prefetched translations by language slug
        """
        if not self.id:
            return {}
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
    def prefetched_translations_by_language_slug(
        self,
    ) -> dict[str, AbstractContentTranslation]:
        """
        This method returns a mapping from language slugs to their latest translations of this object

        :return: The prefetched translations by language slug
        """
        return self.get_prefetched_translations_by_language_slug()

    def get_translation(self, language_slug: str) -> AbstractContentTranslation | None:
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~integreat_cms.cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return self.prefetched_translations_by_language_slug.get(language_slug)

    @cached_property
    def prefetched_public_translations_by_language_slug(
        self,
    ) -> dict[str, AbstractContentTranslation]:
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_public_translations", status=status.PUBLIC
        )

    def get_public_translation(
        self, language_slug: str
    ) -> AbstractContentTranslation | None:
        """
        This function retrieves the newest public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The public translation of a content object
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
                public_translation = copy(public_translation)
                public_translation.read_only = True
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
    def prefetched_public_or_draft_translations_by_language_slug(
        self,
    ) -> dict[str, AbstractContentTranslation]:
        """
        This method returns a mapping from language slugs to their public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_public_or_draft_translations",
            status__in=[status.DRAFT, status.PUBLIC],
        )

    def get_public_or_draft_translation(
        self, language_slug: str
    ) -> AbstractContentTranslation | None:
        """
        This function retrieves the newest public or draft translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The public translation of a content object
        """
        return self.prefetched_public_or_draft_translations_by_language_slug.get(
            language_slug
        )

    @cached_property
    def prefetched_major_public_translations_by_language_slug(
        self,
    ) -> dict[str, AbstractContentTranslation]:
        """
        This method returns a mapping from language slugs to their major public translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_major_public_translations",
            status=status.PUBLIC,
            minor_edit=False,
        )

    def get_major_public_translation(
        self, language_slug: str
    ) -> AbstractContentTranslation | None:
        """
        This function retrieves the newest major public translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The public translation of a content object
        """
        return self.prefetched_major_public_translations_by_language_slug.get(
            language_slug
        )

    @cached_property
    def prefetched_major_translations_by_language_slug(
        self,
    ) -> dict[str, AbstractContentTranslation]:
        """
        This method returns a mapping from language slugs to their major translations of this object

        :return: The object translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or
                 :obj:`None` if no translation exists
        """
        return self.get_prefetched_translations_by_language_slug(
            attr="prefetched_major_translations",
            minor_edit=False,
        )

    def get_major_translation(
        self, language_slug: str
    ) -> AbstractContentTranslation | None:
        """
        This function retrieves the newest major translation of a content object.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: The public translation of a content object
        """
        return self.prefetched_major_translations_by_language_slug.get(language_slug)

    def invalidate_cached_translations(self) -> None:
        """
        Delete all cached translations and query them from the
        database again when they are accessed next time.

        This is helpful when new translations have been created
        and the content model should be reused.
        """
        for prefetched_attr in [
            "backend_translation",
            "best_translation",
            "default_translation",
            "default_public_translation",
            "prefetched_translations_by_language_slug",
            "prefetched_major_public_translations_by_language_slug",
            "prefetched_major_translations_by_language_slug",
            "prefetched_public_or_draft_translations_by_language_slug",
            "prefetched_public_translations_by_language_slug",
            "translation_states",
        ]:
            try:
                delattr(self, prefetched_attr)
            except AttributeError:
                pass

    @cached_property
    def backend_translation(self) -> Any:
        """
        This function returns the translation of this content object in the current backend language.

        :return: The backend translation of a content object
        """
        return self.get_translation(get_language())

    @cached_property
    def default_translation(self) -> AbstractContentTranslation | None:
        """
        This function returns the translation of this content object in the region's default language.
        Since a content object can only be created by creating a translation in the default language, this is guaranteed
        to return a object translation (Exception: When the default language tree node is changed to another language
        after the page has been created, the default translation might not exist).

        :return: The default translation of a content object
        """
        return self.get_translation(self.region.default_language.slug)

    @cached_property
    def default_public_translation(self) -> AbstractContentTranslation | None:
        """
        This function returns the public translation of this content object in the region's default language.

        :return: The default translation of a content object
        """
        return self.get_public_translation(self.region.default_language.slug)

    @cached_property
    def best_translation(
        self,
    ) -> AbstractContentTranslation:
        """
        This function returns the translation of this content object in the current backend language and if it doesn't
        exist, it provides a fallback to the translation in the region's default language.

        :return: The "best" translation of a content object for displaying in the backend
        """
        return (
            self.backend_translation
            or self.default_translation
            or self.translations.first()
        )

    def get_translation_state(self, language_slug: str) -> str:
        """
        This function returns the current state of a translation in the given language.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :return: A string describing the state of the translation, one of :data:`~integreat_cms.cms.constants.translation_status.CHOICES`
        """
        if translation := self.get_translation(language_slug):
            return translation.translation_state
        if self.fallback_translations_enabled and self.get_translation(
            self.region.default_language.slug
        ):
            return translation_status.FALLBACK
        return translation_status.MISSING

    @cached_property
    def translation_states(self) -> dict[str, tuple[Language, str]]:
        """
        This property calculates all translations states of the object

        :return: A dictionary containing each language as key and the given translation state as value
        """
        return {
            node.slug: (node.language, self.get_translation_state(node.slug))
            for node in self.region.language_tree
            if node.active
        }

    @property
    def edit_lock_key(self) -> tuple[str | int | None, str]:
        """
        This property returns the key that is used to lock this specific content object

        :return: A tuple of the id of this object and the classname
        """
        return (self.id, type(self).__name__)

    def get_locking_user(self) -> Any | None:
        """
        This method returns the user that is currently locking this content object.

        :return: The user
        """
        return get_locking_user(*self.edit_lock_key)

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the edit form of this region

        :return: The url
        """
        return self.best_translation.backend_edit_link

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AbstractContentModel object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the content object
        """
        return self.best_translation.title

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractContentModel: AbstractContentModel object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the content object
        """
        class_name = type(self).__name__
        translation_slug = f", slug: {self.best_translation.slug}" if self.id else ""
        return f"<{class_name} (id: {self.id}, region: {self.region.slug}{translation_slug})>"

    class Meta:
        #: This model is an abstract base class
        abstract = True
