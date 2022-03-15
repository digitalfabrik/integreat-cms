"""
This module contains the abstract base classes for the XLIFF serializers.
It makes use of the existing Django serialization functionality (see :doc:`django:topics/serialization` and
:ref:`django:topics/serialization:xml`).

It extends :django-source:`django/core/serializers/base.py` and
:django-source:`django/core/serializers/xml_serializer.py`.
"""
import logging
import xml.dom.minidom

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers import xml_serializer
from django.core.serializers.base import DeserializedObject, DeserializationError
from django.utils.xmlutils import SimplerXMLGenerator

from ..cms.models import Language


logger = logging.getLogger(__name__)


class XMLGeneratorWithCDATA(SimplerXMLGenerator):
    """
    Subclass of SimplerXMLGenerator to provide a custom CDATA node
    """

    def cdata(self, content):
        """
        Create a ``<![CDATA[]>``-block with the given content

        :param content: The given ``CDATA`` content
        :type content: str
        """
        self.ignorableWhitespace(f"<![CDATA[{content}]]>")


class Serializer(xml_serializer.Serializer):
    """
    Abstract base XLIFF serializer class. Inherits basic XML initialization from the default xml_serializer of Django
    (see :ref:`django:topics/serialization:xml`).

    The XLIFF file can be extended by writing to ``self.xml``, which is an instance of
    :class:`~integreat_cms.xliff.base_serializer.XMLGeneratorWithCDATA`.

    For details, look at the implementation of :django-source:`django/core/serializers/base.py` and
    :django-source:`django/core/serializers/xml_serializer.py`.
    """

    #: The XML generator of this serializer instance
    xml = None
    #: Whether only public versions should be exported
    only_public = False

    def serialize(self, queryset, *args, **kwargs):
        r"""
        Initialize serialization and set the :attr:`~integreat_cms.core.settings.XLIFF_DEFAULT_FIELDS`.

        :param queryset: QuerySet of all :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation`
                         objects which should be serialized
        :type queryset: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.pages.page_translation.PageTranslation ]

        :param \*args: The remaining arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The serialized XLIFF string
        :rtype: str
        """
        self.only_public = kwargs.pop("only_public")
        kwargs.setdefault("fields", settings.XLIFF_DEFAULT_FIELDS)
        return super().serialize(queryset, *args, **kwargs)

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
        self.xml = XMLGeneratorWithCDATA(
            self.stream, self.options.get("encoding", settings.DEFAULT_CHARSET)
        )
        self.xml.startDocument()

    def start_object(self, obj):
        """
        Called when serializing of an object starts.

        :param obj: The page translation object which is started
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :raises NotImplementedError: If the property is not implemented in the subclass
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a start_object() method"
        )

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)

        :param obj: The page translation object which is handled
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :param field: The model field
        :type field: ~django.db.models.Field

        :raises NotImplementedError: If the property is not implemented in the subclass
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a handle_field() method"
        )

    def handle_fk_field(self, obj, field):
        """
        ForeignKey fields are not supported by this serializer.
        They will just be ignored and are not contained in the resulting XLIFF file.

        :param obj: The page translation object which is handled
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :param field: The foreign key field
        :type field: ~django.db.models.ForeignKey
        """

    def handle_m2m_field(self, obj, field):
        """
        ManyToMany fields are not supported by this serializer.
        They will just be ignored and are not contained in the resulting XLIFF file.

        :param obj: The page translation object which is handled
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :param field: The many to many field
        :type field: ~django.db.models.ManyToManyField
        """

    def end_object(self, obj):
        """
        Called when serializing of an object ends.

        :param obj: The page translation object which is finished
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """

    def end_serialization(self):
        """
        End serialization by ending the ``<xliff>``-block and the document.
        """
        self.xml.endElement("xliff")
        self.xml.endDocument()

    def getvalue(self):
        """
        Return the fully serialized translation (or ``None`` if the output stream is not seekable).

        :return: The output XLIFF string
        :rtype: str
        """
        if callable(getattr(self.stream, "getvalue", None)):
            # Pretty print output
            return xml.dom.minidom.parseString(self.stream.getvalue()).toprettyxml()
        return None


class Deserializer(xml_serializer.Deserializer):
    """
    Abstract base XLIFF deserializer class. Inherits basic XML initialization from the default xml_serializer of Django.
    The contents of the XLIFF file are available through ``self.event_stream``, which gets assigned to the result of
    :func:`python:xml.dom.pulldom.parse`.
    """

    #: The node name of serialized fields (either "unit" or "trans-unit")
    unit_node = None

    def __next__(self):
        """
        Iteration interface which returns the next item in the stream.
        Since each object has its own ``<file>``-block, this is where the XLIFF file gets split.

        :raises StopIteration: When the event stream is completely finished and there are no <file>-blocks left

        :return: The next deserialized page translation
        :rtype: django.core.serializers.base.DeserializedObject
        """
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "file":
                self.event_stream.expandNode(node)
                return self.handle_object(node)
        raise StopIteration

    def get_object(self, node):
        """
        Retrieve an object from the serialized unit node.
        To be implemented in the subclass of this base serializer.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :raises NotImplementedError: If the property is not implemented in the subclass
        """
        raise NotImplementedError(
            "subclasses of Deserializer must provide a _get_object() method"
        )

    def handle_object(self, node):
        """
        Convert a ``<file>``-node to a ``DeserializedObject``.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :raises ~django.core.serializers.base.DeserializationError: If the deserialization fails

        :raises ~django.core.exceptions.FieldDoesNotExist: If the XLIFF file contains a field which doesn't exist on the

        :return: The deserialized page translation
        :rtype: django.core.serializers.base.DeserializedObject

                                                           PageTranslation model
        """
        # Get page translation (process varies for the different xliff versions)
        page_translation = self.get_object(node)
        logger.debug(
            "Existing page translation: %r",
            page_translation,
        )
        # Increment the version number
        page_translation.version = page_translation.version + 1
        # Make sure object is not in translation anymore if it was before
        page_translation.currently_in_translation = False
        # Set the id to None to make sure a new object is stored in the database when save() is called
        page_translation.id = None

        # Deserialize each field.
        for field_node in node.getElementsByTagName(self.unit_node):
            # Check to which attribute this resource belongs to
            field_name = self.require_attribute(field_node, "resname")
            # Get the field from the PageTranslation model
            try:
                field = page_translation._meta.get_field(field_name)
            except FieldDoesNotExist as e:
                # If the field doesn't exist, check if a legacy field is supported
                field_name = settings.XLIFF_LEGACY_FIELDS.get(field_name)
                try:
                    field = page_translation._meta.get_field(field_name)
                except FieldDoesNotExist:
                    # If the legacy field doesn't exist as well, just raise the initial exception
                    # pylint: disable=raise-missing-from
                    raise e

            # Now get the actual target value of the field
            target = field_node.getElementsByTagName("target")
            if not target:
                raise DeserializationError(
                    f"Field {field_name} does not contain a <target> node."
                )
            # Set the field attribute of the page translation to the new target value
            setattr(
                page_translation,
                field_name,
                field.to_python(xml_serializer.getInnerText(target[0]).strip()),
            )

        logger.debug("Deserialized page translation: %r", page_translation)
        # Return a DeserializedObject
        return DeserializedObject(page_translation)

    def _handle_object(self, node):
        """
        Convert a ``<file>``-node to a ``DeserializedObject``.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :return: The deserialized page translation
        :rtype: django.core.serializers.base.DeserializedObject
        """
        return self.handle_object(node)

    def _handle_fk_field_node(self, node, field):
        """
        ForeignKey fields are not supported by this deserializer.
        They will just be ignored and are not contained in the resulting deserialized object.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :param field: The foreign key Field
        :type field: ~django.db.models.fields.related.ForeignKey
        """

    def _handle_m2m_field_node(self, node, field):
        """
        ManyToMany fields are not supported by this deserializer.
        They will just be ignored and are not contained in the resulting deserialized object.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :param field: The foreign key Field
        :type field: ~django.db.models.ManyToManyField
        """

    def _get_model_from_node(self, node, attr):
        """
        This deserializer only supports the PageTranslation model.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :param attr: The name of the attribute which contains the model
        :type attr: str
        """

    @staticmethod
    def get_language(attribute):
        """
        Get the language object to a given ``bcp47_tag`` or ``slug``.

        :param attribute: The ``bcp47_tag`` or ``slug`` of the requested language
        :type attribute: str

        :raises ~integreat_cms.cms.models.languages.language.Language.DoesNotExist: If no language exists with the given
                                                                                    attribute

        :return: The requested language
        :rtype: ~integreat_cms.cms.models.languages.language.Language
        """
        try:
            return Language.objects.get(bcp47_tag=attribute)
        except Language.DoesNotExist:
            return Language.objects.get(slug=attribute)

    @staticmethod
    def require_attribute(node, attribute):
        """
        Get the attribute of a node and throw an error if it evaluates to ``False``

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :param attribute: The name of the requested attribute
        :type attribute: str

        :raises ~django.core.serializers.base.DeserializationError: If the deserialization fails

        :return: The value name of the requested attribute
        :rtype: str
        """
        value = node.getAttribute(attribute)
        if not value:
            raise DeserializationError(
                f"<{node.nodeName}> node is missing the {attribute} attribute"
            )
        return value
