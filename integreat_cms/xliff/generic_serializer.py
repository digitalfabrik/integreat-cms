from django.core.serializers.base import DeserializationError

from . import base_serializer, xliff1_serializer, xliff2_serializer


class Serializer(xliff2_serializer.Serializer):
    """
    For serialization, just fall back to the serializer for XLIFF version 2.0
    """


# pylint: disable=too-few-public-methods
class Deserializer(base_serializer.Deserializer):
    """
    For deserialization, inspect the data and choose the correct version
    """

    def __init__(self, *args, **kwargs):
        # Initialize the base xliff deserializer
        super().__init__(*args, **kwargs)
        # Get XLIFF version and initialize deserializer of correct version
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "xliff":
                version = node.getAttribute("version")
                if not version:
                    raise DeserializationError(
                        "The <xliff>-block does not contain a version attribute."
                    )
                if version == "1.2":
                    self.xliff_deserializer = xliff1_serializer.Deserializer(
                        *args, **kwargs
                    )
                    return
                if version == "2.0":
                    self.xliff_deserializer = xliff2_serializer.Deserializer(
                        *args, **kwargs
                    )
                    return
                raise DeserializationError(
                    f"This serializer cannot process XLIFF version {version}."
                )
        raise DeserializationError("The data does not contain an <xliff>-block.")

    def get_object(self, node):
        """
        Retrieve an object from the serialized unit node.
        Handled by either :func:`~integreat_cms.xliff.xliff1_serializer.Deserializer.get_object` or
        :func:`~integreat_cms.xliff.xliff2_serializer.Deserializer.get_object`

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :return: The original page translation
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        return self.xliff_deserializer.get_object(node)

    def handle_object(self, node):
        """
        Convert a ``<file>``-node to a DeserializedObject.
        Handled by either :func:`~integreat_cms.xliff.xliff1_serializer.Deserializer.handle_object` or
        :func:`~integreat_cms.xliff.xliff2_serializer.Deserializer.handle_object`

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :return: The deserialized page translation
        :rtype: django.core.serializers.base.DeserializedObject
        """
        return self.xliff_deserializer.handle_object(node)
