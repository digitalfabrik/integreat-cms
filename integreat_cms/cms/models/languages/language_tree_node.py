from django.apps import apps
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .language import Language
from ..abstract_tree_node import AbstractTreeNode
from ..decorators import modify_fields


@modify_fields(parent={"verbose_name": _("source language")})
class LanguageTreeNode(AbstractTreeNode):
    """
    Data model representing a region's language tree. Each tree node is a single object instance and the whole tree is
    identified by the root node. The base functionality inherits from the package `django-mptt
    <https://django-mptt.readthedocs.io/en/latest/index.html>`_ (Modified Preorder Tree Traversal).
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
            "Defines whether the language is displayed to the users of the app"
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

    @cached_property
    def slug(self):
        """
        Returns the slug of this node's language

        :return: The language slug of this language node
        :rtype: str
        """
        return self.language.slug

    @cached_property
    def native_name(self):
        """
        Returns the native name of this node's language

        :return: The native name of this language node
        :rtype: str
        """
        return self.language.native_name

    @cached_property
    def english_name(self):
        """
        Returns the name of this node's language in English

        :return: The English name of this language node
        :rtype: str
        """
        return self.language.english_name

    @cached_property
    def translated_name(self):
        """
        Returns the name of this node's language in the current backend language

        :return: The translated name of this language node
        :rtype: str
        """
        return self.language.translated_name

    @cached_property
    def text_direction(self):
        """
        Returns the text direction (e.g. left-to-right) of this node's language

        :return: The text direction name of this language node
        :rtype: str
        """
        return self.language.text_direction

    @cached_property
    def mt_provider(self):
        """
        Return the name of the machine translation provider if it exists,
        or empty string otherwise

        :return: Name of the MT provider for the language
        :rtype: str
        """
        deepl_config = apps.get_app_config("deepl_api")
        if (
            self.slug == settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
            and settings.SUMM_AI_ENABLED
            and self.region.summ_ai_enabled
        ):
            return "SUMM.AI"
        if self.slug in deepl_config.supported_target_languages:
            return "DeepL"
        return ""

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``LanguageTreeNode object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the language node
        :rtype: str
        """
        return self.translated_name

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<LanguageTreeNode: LanguageTreeNode object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the language node
        :rtype: str
        """
        language_str = f", language: {self.language.slug}" if self.language else ""
        parent_str = f", parent: {self.parent_id}" if self.parent_id else ""
        region_str = f", region: {self.region.slug}" if self.region else ""
        return (
            f"<LanguageTreeNode (id: {self.id}{language_str}{parent_str}{region_str})>"
        )

    class Meta:
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
