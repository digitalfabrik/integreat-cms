import logging

from django.core.serializers import base

from ..cms.models import Page, PageTranslation
from . import base_serializer


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

    def serialize(self, queryset, *args, **kwargs):
        r"""
        Initialize serialization and find out in which source and target language the given elements are.

        :param queryset: QuerySet of all :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects which
                         should be serialized
        :type queryset: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.pages.page_translation.PageTranslation ]

        :param \*args: The remaining arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :raises ~django.core.serializers.base.SerializationError: If the serialization fails

        :return: The serialized XLIFF string
        :rtype: str

        """
        # Get all language objects of the given page translations
        language_set = set(map(lambda p: p.language, queryset))
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
        region_set = set(map(lambda p: p.page.region, queryset))
        logger.debug("XLIFF 2.0 serialization for regions %r", region_set)
        # Check if all given translations are of the same region
        if len(region_set) != 1:
            raise base.SerializationError(
                "The page translations are from different regions."
            )

        region = next(iter(region_set))
        target_language = next(iter(language_set))
        if target_language == region.default_language:
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

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
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

    def start_object(self, obj):
        """
        Called as each object is handled.
        Adds an XLIFF ``<file>``-block with meta-information about the object.

        :param obj: The page translation object which is started
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        logger.debug("XLIFF 2.0 serialization starting object %r", obj)
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
            },
        )

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)

        :param obj: The page translation object which is handled
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :param field: The model field
        :type field: ~django.db.models.Field

        :raises ~django.core.serializers.base.SerializationError: If the serialization fails
        """
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
            else obj.source_translation
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

    def end_object(self, obj):
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.

        :param obj: The page translation object which is finished
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        logger.debug("XLIFF 2.0 serialization ending object %r", obj)
        self.xml.endElement("file")


# pylint: disable=too-few-public-methods
class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 2.0

    Deserializes XLIFF files into :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects.
    """

    #: The node name of serialized fields
    unit_node = "unit"

    def __init__(self, *args, **kwargs):
        r"""
        Initialize XLIFF 2.0 deserializer

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

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

    def get_object(self, node):
        """
        Retrieve an object from the serialized unit node.
        To be implemented in the subclass of this base serializer.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :return: The original page translation
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        # Get the page to which this serialized object belongs to
        page_id = self.require_attribute(node, "original")
        page = Page.objects.get(id=page_id)
        logger.debug(
            "Referenced original page: %r",
            page,
        )

        # Retrieve a existing target translation or create a new one
        page_translation = page.get_translation(self.target_language.slug)
        if not page_translation:
            # Initial attributes passed to model constructor
            attrs = {
                "page": page,
                "language": self.target_language,
            }
            # Get source translation to inherit status field
            source_translation = page.get_translation(self.source_language.slug)
            if source_translation:
                attrs["status"] = source_translation.status
            page_translation = PageTranslation(**attrs)
        return page_translation
