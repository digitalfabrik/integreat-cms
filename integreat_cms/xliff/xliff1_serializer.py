from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from django.conf import settings
from django.core.serializers import base

from ..cms.models import Page, PageTranslation
from . import base_serializer

if TYPE_CHECKING:
    from xml.dom.minidom import Element

    from django.db.models.fields import CharField, TextField

logger = logging.getLogger(__name__)


class Serializer(base_serializer.Serializer):
    """
    XLIFF serializer class for XLIFF version 1.2.
    This was inspired by `django-xliff <https://github.com/callowayproject/django-xliff>`__.
    """

    def start_serialization(self) -> None:
        """
        Start serialization - open the XML document and the root element.
        """
        super().start_serialization()
        if TYPE_CHECKING:
            assert self.xml
        self.xml.startElement(
            "xliff",
            {
                "version": "1.2",
                "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
            },
        )

    def start_object(self, obj: PageTranslation) -> None:
        """
        Called as each object is handled. Adds an XLIFF ``<file>``-block with meta-information about the object and an
        additional ``<body>`` for XLIFF version 1.2.

        :param obj: The page translation object which is started
        :raises ~django.core.serializers.base.SerializationError: If the serialization fails
        """
        if TYPE_CHECKING:
            assert self.xml
        if not (
            source_language := obj.page.region.get_source_language(obj.language.slug)
        ):
            raise base.SerializationError(
                "The page translation is in the region's default language."
            )
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
                "datatype": "plaintext",
                "source-language": source_language.bcp47_tag,
                "target-language": obj.language.bcp47_tag,
            },
        )
        # This header is required to make sure the XLIFF file can be segmented with MemoQ's WPML filter to get the same
        # translation memory as with the legacy export via WordPress/WPML. See also:
        # https://docs.memoq.com/current/en/Places/wpml-xliff-filter.html
        self.xml.startElement("header", {})
        self.xml.startElement("phase-group", {})
        self.xml.addQuickElement(
            "phase",
            attrs={
                "phase-name": "shortcodes",
                "process-name": "Shortcodes identification",
            },
        )
        self.xml.addQuickElement(
            "phase", attrs={"phase-name": "post_type", "process-name": "Post type"}
        )
        self.xml.endElement("phase-group")
        self.xml.endElement("header")
        self.xml.startElement("body", {})

    def handle_field(self, obj: PageTranslation, field: CharField | TextField) -> None:
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)

        :param obj: The page translation object which is handled
        :param field: The model field
        """
        if TYPE_CHECKING:
            assert self.xml
        # Use legacy field name if available
        REVERSE_XLIFF_LEGACY_FIELDS: dict[str, str] = dict(
            map(reversed, settings.XLIFF_LEGACY_FIELDS.items())  # type: ignore[arg-type]
        )
        field_name = REVERSE_XLIFF_LEGACY_FIELDS.get(field.name, field.name)
        attrs = {
            "id": field_name,
            "resname": field_name,
            "restype": "string",
            "datatype": "html",
        }
        self.xml.startElement("trans-unit", attrs)

        self.xml.startElement("source", {})
        source_translation = (
            obj.public_source_translation
            if self.only_public
            else obj.public_or_draft_source_translation
        )
        self.xml.cdata(field.value_to_string(source_translation))
        self.xml.endElement("source")

        self.xml.startElement("target", {})
        self.xml.cdata(field.value_to_string(obj))
        self.xml.endElement("target")

        self.xml.endElement("trans-unit")

    def end_object(self, obj: PageTranslation) -> None:
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.

        :param obj: The page translation object which is finished
        """
        if TYPE_CHECKING:
            assert self.xml
        self.xml.endElement("body")
        self.xml.endElement("file")


class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 1.2
    """

    #: The node name of serialized fields
    unit_node = "trans-unit"

    def get_object(self, node: Element) -> PageTranslation:
        """
        Retrieve an object from the serialized unit node.

        :param node: The current xml node of the object
        :raises ~django.core.serializers.base.DeserializationError: If the deserialization fails

        :return: The original page translation
        """
        # Get original page
        page_id = self.require_attribute(node, "original")
        try:
            page = Page.objects.get(id=page_id)
        except (ValueError, Page.DoesNotExist) as e:
            # If the id isn't a number or if no page with this id is found, check if the external file reference is given
            if not (external_file := node.getElementsByTagName("external-file")):
                # If no such reference is given, just raise the initial error
                raise e
            # Get href of external file and parse url
            page_link = (
                urlparse(self.require_attribute(external_file[0], "href"))
                .path.strip("/")
                .split("/")
            )
            logger.debug(
                "<external-file>-node found, parsed page link: %r",
                page_link,
            )
            # Expect the link to be in the format /<region_slug>/<language_slug>/[<parent_page_slug>]/<page_slug>/
            if len(page_link) < 3:
                raise base.DeserializationError(
                    "The page link of the <external-file> reference needs at least 3 segments"
                ) from e
            page_translation_slug = page_link.pop()
            region_slug, language_slug = page_link[:2]
            page = Page.objects.filter(
                region__slug=region_slug,
                translations__slug=page_translation_slug,
                translations__language__slug=language_slug,
            ).first()
            if not page:
                # If no page matches the link, just raise the initial error
                raise e

        logger.debug(
            "Referenced original page: %r",
            page,
        )

        # Get target language of this file
        target_language = self.get_language(
            self.require_attribute(node, "target-language")
        )

        # Get existing target translation or create a new one
        if page_translation := page.get_translation(target_language.slug):
            return page_translation
        # Initial attributes passed to model constructor
        attrs = {
            "page": page,
            "language": target_language,
        }
        # Get source translation to inherit status field
        source_language = self.get_language(
            self.require_attribute(node, "source-language")
        )
        if source_translation := page.get_translation(source_language.slug):
            attrs["status"] = source_translation.status
        return PageTranslation(**attrs)
