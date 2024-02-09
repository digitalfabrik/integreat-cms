"""
This module contains utilities for machine translations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...cms.constants import machine_translation_permissions as mt_perms

if TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django.db.models.query import QuerySet
    from django.utils.functional import SimpleLazyObject

    from ...cms.models import Event, Language, Page, POI, Region

logger = logging.getLogger(__name__)


class MachineTranslationProviderType(type):
    """
    A meta class for machine translation providers
    """

    def __str__(cls) -> str:
        """
        :return: A readable string representation of the machine translation provider
        """
        return cls.name  # type: ignore[attr-defined]

    def __repr__(cls) -> str:
        """
        :return: The canonical string representation of the machine translation provider
        """
        class_name = cls.__name__
        return f"<{class_name} (name: {cls.name}, api_client: {cls.api_client!r})>"  # type: ignore[attr-defined]


class MachineTranslationProvider(metaclass=MachineTranslationProviderType):
    """
    A base class for machine translation providers.
    It should be used as static class, without instantiating it.
    """

    #: The readable name for this provider
    name: str = ""
    #: The API client class for this provider
    api_client: type | None = None
    #: Whether to require the staff permission for bulk actions
    bulk_only_for_staff: bool = False
    #: Whether the provider is globally enabled
    enabled: bool = True
    #: The name of the region attribute which denotes whether the provider is enabled in a region
    region_enabled_attr: str | None = None
    #: The supported source languages
    supported_source_languages: list[str] = []
    #: The supported target languages
    supported_target_languages: list[str] = []

    # pylint: disable=too-many-return-statements
    @classmethod
    def is_enabled(cls, region: Region, language: Language) -> bool:
        """
        Whether this provider is enabled for a given region and language.
        Call this from the parent class.

        :param region: The given region
        :param language: The given language
        :returns: Wether this provider is enabled for the given region and language
        """
        if not (language_node := region.language_node_by_slug.get(language.slug)):
            logger.debug(
                "Machine translations are disabled because %r does not exist in %r.",
                language,
                region,
            )
            return False

        if not language_node.active:
            logger.debug(
                "Machine translations are disabled because %r is not active in %r.",
                language,
                region,
            )
            return False

        if language_node.is_root():
            logger.debug(
                "Machine translations are disabled because %r is the default language in %r.",
                language,
                region,
            )
            return False

        if not language_node.machine_translation_enabled:
            logger.debug(
                "Machine translations are disabled for %r in %r.", language, region
            )
            return False

        if not cls.enabled:
            logger.debug("Machine translations via %s are disabled globally.", cls.name)
            return False

        if cls.region_enabled_attr and not getattr(region, cls.region_enabled_attr):
            logger.debug(
                "Machine translations via %s are disabled in %r.",
                cls.name,
                region,
            )
            return False

        source_language = region.get_source_language(language_node.slug)
        if TYPE_CHECKING:
            assert source_language
        if source_language.slug not in cls.supported_source_languages:
            logger.debug(
                "Machine translations via %s are disabled for %r because the slug of its source language %r is not in %r.",
                cls.name,
                language_node.language,
                source_language,
                cls.supported_source_languages,
            )
            return False

        codes = [language_node.slug, language_node.language.bcp47_tag.lower()]
        if all(code not in cls.supported_target_languages for code in codes):
            logger.debug(
                "Machine translations via %s are disabled for %r because neither its slug nor its bcp47 tag is in %r.",
                cls.name,
                language_node.language,
                cls.supported_target_languages,
            )
            return False

        return True

    @staticmethod
    def is_permitted(
        region: Region, user: SimpleLazyObject, content_type: ModelBase
    ) -> bool:
        """
        Checks if a machine translation is permitted, i.e. if for the
        given region, MT of the given content type is allowed and
        MT into the target language is enabled for the requesting user.

        :param region: The current region
        :param user: The current user
        :param content_type: The content model which should be translated
        :return: Whether the translation is permitted
        """
        foreign_field = content_type.foreign_field()
        mt_perms_setting = getattr(region, f"machine_translate_{foreign_field}s")
        required_perm = f"cms.change_{foreign_field}"

        if mt_perms_setting == mt_perms.NO_ONE:
            logger.debug(
                "Machine translations are not permitted for content type %r in %r.",
                content_type,
                region,
            )
            return False

        mt_perm = "cms.manage_translations"
        if mt_perms_setting == mt_perms.MANAGERS and not user.has_perm(mt_perm):
            logger.debug(
                "Machine translations are only permitted for content type %r in %r for users with the permission %r.",
                content_type,
                region,
                mt_perm,
            )
            return False

        if not user.has_perm(required_perm):
            logger.debug(
                "Machine translations are only permitted for content type %r in %r for users with the permission %r.",
                content_type,
                region,
                required_perm,
            )
            return False

        return True

    def is_needed(
        self, queryset: QuerySet[Event | Page | POI], target_language: Language
    ) -> list[Event | Page | POI]:
        """
        Checks if a machine translation is needed, thus checking if the
        translation status is UP_TO_DATE or MACHINE_TRANSLATED and then
        returns a lit of translations which are to be updated

        :param queryset: The content model which should be translated
        :param target_language: The target language
        :return: translations which need to be translated and updated
        """
        # Before translating, check if translation is not up-to-date
        to_translate = []
        for content_object in queryset:
            existing_target_translation = content_object.get_translation(
                target_language.slug
            )
            if (
                existing_target_translation
                and existing_target_translation.translation_state
                in (
                    "UP_TO_DATE",
                    "MACHINE_TRANSLATED",
                )
            ):
                logger.debug(
                    "There already is an up-to-date translation for %s",
                    content_object.best_translation.title,
                )
            else:
                to_translate += [content_object]
        return to_translate
