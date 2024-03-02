from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.serializers import base

from ..cms.models import Page, PageTranslation
from . import base_serializer

if TYPE_CHECKING:
    from typing import Any
    from xml.dom.minidom import Element

    from django.db.models.fields import CharField, TextField

logger = logging.getLogger(__name__)


class Serializer(base_serializer.Serializer):
    """
    XLIFF serializer class for XLIFF version 2.0

    Serializes :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects into translatable XLIFF files.
    """

    #: The source language of this serializer instance
    source_language = None
    #: The target language of this serializer instance
    target_language = None

    def serialize(
        self, queryset: list[PageTranslation], *args: Any, **kwargs: Any
    ) -> str:
        r"""
        Initialize serialization and find out in which source and target language the given elements are.

        :param queryset: QuerySet of all :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects which
                         should be serialized
        :param \*args: The remaining arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.serializers.base.SerializationError: If the serialization fails

        :return: The serialized XLIFF string
        """
        # Get all language objects of the given page translations
        language_set = {p.language for p in queryset}
        logger.debug("XLIFF 2.0 serialization for languages %r", language_set)
        if not language_set:
            raise base.SerializationError("No page translations given to serialize.")
        # Check if all given translations are of the same language
        if len(language_set) != 1:
            raise base.SerializationError(
                "The page translations have different languages, but in XLIFF 2.0 "
                "all objects of one file need to have the same language."
            )

        # Get all region objects of the given page translations
        region_set = {p.page.region for p in queryset}
        logger.debug("XLIFF 2.0 serialization for regions %r", region_set)
        # Check if all given translations are of the same region
        if len(region_set) != 1:
            raise base.SerializationError(
                "The page translations are from different regions."
            )

        region = next(iter(region_set))
        if (target_language := next(iter(language_set))) == region.default_language:
            raise base.SerializationError(
                "The page translation is in the region's default language."
            )
        self.target_language = target_language
        self.source_language = region.get_source_language(target_language.slug)
        logger.debug(
            "Starting XLIFF 2.0 serialization for translation from %r to %r",
            self.source_language,
            target_language,
        )
        return super().serialize(queryset, *args, **kwargs)

    def start_serialization(self) -> None:
        """
        Start serialization - open the XML document and the root element.
        """
        if TYPE_CHECKING:
            assert self.xml
            assert self.source_language
            assert self.target_language
        logger.debug(
            "XLIFF 2.0 starting serialization",
        )
        super().start_serialization()
        self.xml.startElement(
            "xliff",
            {
                "version": "2.0",
                "xmlns": "urn:oasis:names:tc:xliff:document:2.0",
                "srcLang": self.source_language.bcp47_tag,
                "srcDir": self.source_language.text_direction,
                "trgLang": self.target_language.bcp47_tag,
                "trgDir": self.target_language.text_direction,
            },
        )

    def start_object(self, obj: PageTranslation) -> None:
        """
        Called as each object is handled.
        Adds an XLIFF ``<file>``-block with meta-information about the object.

        :param obj: The page translation object which is started
        """
        if TYPE_CHECKING:
            assert self.xml
        logger.debug("XLIFF 2.0 serialization starting object %r", obj)
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
            },
        )

    def handle_field(self, obj: PageTranslation, field: CharField | TextField) -> None:
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)

        :param obj: The page translation object which is handled
        :param field: The model field
        :raises ~django.core.serializers.base.SerializationError: If the serialization fails
        """
        if TYPE_CHECKING:
            assert self.xml
        logger.debug(
            "XLIFF 2.0 serialization handling field %r of object %r", field, obj
        )
        attrs = {
            "id": field.name,
            "resname": field.name,
            "restype": "string",
            "datatype": "html",
        }
        self.xml.startElement("unit", attrs)
        self.xml.startElement("segment", {})

        self.xml.startElement("source", {})
        source_translation = (
            obj.public_source_translation
            if self.only_public
            else obj.public_or_draft_source_translation
        )
        if not source_translation:
            raise base.SerializationError(
                f"Page translation {obj!r} does not have a source translation in "
                f"{self.source_language!r} and therefore cannot be serialized to XLIFF."
            )
        logger.debug("XLIFF 2.0 source translation %r", source_translation)
        self.xml.cdata(field.value_to_string(source_translation))
        self.xml.endElement("source")

        self.xml.startElement("target", {})
        self.xml.cdata(field.value_to_string(obj))
        self.xml.endElement("target")

        self.xml.endElement("segment")
        self.xml.endElement("unit")

    def end_object(self, obj: PageTranslation) -> None:
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.

        :param obj: The page translation object which is finished
        """
        if TYPE_CHECKING:
            assert self.xml
        logger.debug("XLIFF 2.0 serialization ending object %r", obj)
        self.xml.endElement("file")


class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 2.0

    Deserializes XLIFF files into :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects.
    """

    #: The node name of serialized fields
    unit_node = "unit"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize XLIFF 2.0 deserializer

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :raises ~django.core.serializers.base.DeserializationError: If the deserialization fails
        """
        # Initialize base deserializer
        super().__init__(*args, **kwargs)
        # Get language objects from <xliff>-node
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "xliff":
                # Get source language stored in the xliff node
                self.source_language = self.get_language(
                    self.require_attribute(node, "srcLang")
                )
                # Get target language stored in the xliff node
                self.target_language = self.get_language(
                    self.require_attribute(node, "trgLang")
                )
                logger.debug(
                    "Starting XLIFF 2.0 deserialization for translation from %r to %r",
                    self.source_language,
                    self.target_language,
                )
                return
        raise base.DeserializationError(
            "The XLIFF file does not contain an <xliff>-block,"
        )

    def get_object(self, node: Element) -> PageTranslation:
        """
        Retrieve an object from the serialized unit node.
        To be implemented in the subclass of this base serializer.

        :param node: The current xml node of the object
        :return: The original page translation
        """
        # Get the page to which this serialized object belongs to
        page_id = self.require_attribute(node, "original")
        page = Page.objects.get(id=page_id)
        logger.debug(
            "Referenced original page: %r",
            page,
        )

        # Retrieve a existing target translation or create a new one
        if page_translation := page.get_translation(self.target_language.slug):
            return page_translation
        # Initial attributes passed to model constructor
        attrs = {
            "page": page,
            "language": self.target_language,
        }
        if source_translation := page.get_translation(self.source_language.slug):
            attrs["status"] = source_translation.status
        return PageTranslation(**attrs)
