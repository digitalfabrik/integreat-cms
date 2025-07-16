from __future__ import annotations

from typing import Any, TYPE_CHECKING

from cacheops import invalidate_obj
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ...constants import machine_translation_providers
from ..abstract_tree_node import AbstractTreeNode
from ..decorators import modify_fields
from .language import Language

if TYPE_CHECKING:
    from ...models import Region

if TYPE_CHECKING:
    from integreat_cms.core.utils.machine_translation_provider import (
        MachineTranslationProviderType,
    )


@modify_fields(parent={"verbose_name": _("source language")})
class LanguageTreeNode(AbstractTreeNode):
    """
    Data model representing a region's language tree. Each tree node is a single object instance and the whole tree is
    identified by the root node. The base functionality inherits from the package `django-treebeard
    <https://django-treebeard.readthedocs.io/en/latest/>`.
    """

    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="language_tree_nodes",
        verbose_name=_("language"),
    )
    visible = models.BooleanField(
        default=True,
        verbose_name=_("visible"),
        help_text=_(
            "Defines whether the language is displayed to the users of the app",
        ),
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_("Defined if content in this language can be created or edited"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )
    machine_translation_enabled = models.BooleanField(
        default=True,
        verbose_name=_("machine translatable"),
        help_text=_("Enable or disable machine translations into this language"),
    )
    preferred_mt_provider = models.CharField(
        max_length=255,
        choices=(
            (provider.name, provider.name)
            for provider in machine_translation_providers.CHOICES
        ),
        default=next(iter(machine_translation_providers.CHOICES)).name,
        verbose_name=_("machine translation provider"),
        help_text=_("Preferred provider for translations into this language"),
    )

    @cached_property
    def slug(self) -> str:
        """
        Returns the slug of this node's language

        :return: The language slug of this language node
        """
        return self.language.slug

    @cached_property
    def native_name(self) -> str:
        """
        Returns the native name of this node's language

        :return: The native name of this language node
        """
        return self.language.native_name

    @cached_property
    def english_name(self) -> str:
        """
        Returns the name of this node's language in English

        :return: The English name of this language node
        """
        return self.language.english_name

    @cached_property
    def translated_name(self) -> str:
        """
        Returns the name of this node's language in the current backend language

        :return: The translated name of this language node
        """
        return self.language.translated_name

    @cached_property
    def text_direction(self) -> str:
        """
        Returns the text direction (e.g. left-to-right) of this node's language

        :return: The text direction name of this language node
        """
        return self.language.text_direction

    @cached_property
    def mt_providers(self) -> list[MachineTranslationProviderType]:
        """
        Return the list of supported machine translation providers

        :return: The MT provider for this target language
        """
        return [
            provider
            for provider in machine_translation_providers.CHOICES
            if provider.is_enabled(self.region, self.language)
        ]

    @cached_property
    def mt_provider(self) -> MachineTranslationProviderType | None:
        """
        Return the preferred machine translation provider if valid, or the first available provider, or ``None``

        :return: The MT provider for this target language
        """
        return next(
            (p for p in self.mt_providers if p.name == self.preferred_mt_provider),
            next(iter(self.mt_providers), None),
        )

    def can_be_deleted(self) -> tuple[bool, str | None]:
        """
        Checks if language node can be deleted
        """
        if not self.is_leaf():
            return False, _("a source language of other language(s) cannot be deleted.")
        return True, None

    def manually_invalidate_models(self, region: Region) -> None:
        """
        This is a helper function to iterate through all affected objects and invalidate their cache.
        This is necessary as the original cache invalidation of cacheops only triggers for direct foreign key relationships.

        :param region: The affected region
        """
        for page in region.pages.all():
            invalidate_obj(page)
        for event in region.events.all():
            invalidate_obj(event)
        for poi in region.pois.all():
            invalidate_obj(poi)
        for push_notification in region.push_notifications.all():
            invalidate_obj(push_notification)
        if region.imprint:
            invalidate_obj(region.imprint)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """
        Deletes the language node and its translations
        """
        # get current region
        region = self.region
        # get all page translations assigned to the language node
        page_translations = self.language.page_translations
        # filter those translations that belong to the region and delete them
        page_translations.filter(page__region=region).delete()
        # get all event translations assigned to the language node
        event_translations = self.language.event_translations
        # filter those translations that belong to the region and delete them
        event_translations.filter(event__region=region).delete()
        # get all poi translations assigned to the language node
        poi_translations = self.language.poi_translations
        # filter those translations that belong to the region and delete them
        poi_translations.filter(poi__region=region).delete()

        result = super().delete(*args, **kwargs)

        self.manually_invalidate_models(region)

        return result

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``LanguageTreeNode object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the language node
        """
        return self.translated_name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<LanguageTreeNode: LanguageTreeNode object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the language node
        """
        language_str = f", language: {self.language.slug}" if self.language else ""
        parent_str = f", parent: {self.parent_id}" if self.parent_id else ""
        region_str = f", region: {self.region.slug}" if self.region else ""
        return (
            f"<LanguageTreeNode (id: {self.id}{language_str}{parent_str}{region_str})>"
        )

    class Meta(AbstractTreeNode.Meta):
        #: The verbose name of the model
        verbose_name = _("language tree node")
        #: The plural verbose name of the model
        verbose_name_plural = _("language tree nodes")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "language_tree_nodes"
        #: There cannot be two language tree nodes with the same region and language
        unique_together = (
            (
                "language",
                "region",
            ),
        )
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
