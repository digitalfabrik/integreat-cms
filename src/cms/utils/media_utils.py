"""
Utility functions for the media management. Most of the functions are used to transform media data to other data types.
"""
import uuid
import pathlib
import math
import os

from PIL import Image

from django.utils.text import slugify

from backend.settings import MEDIA_ROOT, MEDIA_URL


def attach_file(document, file):
    """
    Function to create a physical file on the server by an byte upload.

    :param document: Document that is created
    :type document: ~cms.models.media.document.Document

    :param file: File in bytes that is uploaded.
    :type file: bytes
    """
    physical_path = f"{uuid.uuid4()}-{slugify(file.name)}"
    with open(os.path.join(MEDIA_ROOT, physical_path), "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
        document.physical_path = physical_path
        document.type = file.content_type


# pylint: disable=too-many-locals
def get_thumbnail(document, width, height, crop):
    """
    Creates a thumbnail for a given document.

    :param document: Document for the thumbnail
    :type document: ~cms.models.media.document.Document

    :param width: Width of the desired thumbnail
    :type width: int

    :param height: Height of the desired thumbnail
    :type height: int

    :param crop: Option to either crop the thumbnail or not.
    :type crop: bool

    :return: The physical path to the created thumbnail.
    :rtype: str
    """
    if document.type.startswith("image"):
        file_extension = document.type.replace("image/", "")
        thumb_file_name = (
            f"{document.physical_path}_thumb_{width}_{height}_{crop}.{file_extension}"
        )
        thumb_file_path = os.path.join(MEDIA_ROOT, thumb_file_name)
        path = pathlib.Path(thumb_file_path)
        if not path.is_file():
            try:
                image = Image.open(os.path.join(MEDIA_ROOT, document.physical_path))
                original_width = image.width
                original_height = image.height
                width_ratio = original_width / width
                height_ratio = original_height / height
                if crop:
                    if width_ratio < height_ratio:
                        resized_image = image.resize(
                            (width, math.ceil(original_height / width_ratio))
                        )
                    else:
                        resized_image = image.resize(
                            (math.ceil(original_width / height_ratio), height)
                        )
                    offset_x = math.floor(resized_image.width - width) / 2
                    offset_y = math.floor(resized_image.height - height) / 2
                    print(resized_image.width, resized_image.height)
                    thumbnail = resized_image.crop(
                        (offset_x, offset_y, width + offset_x, height + offset_y)
                    )
                else:
                    if width_ratio > height_ratio:
                        thumbnail = image.resize(
                            (width, math.ceil(original_height / width_ratio))
                        )
                    else:
                        thumbnail = image.resize(
                            (math.ceil(original_width / height_ratio), height)
                        )
                thumbnail.save(thumb_file_path, image.format)
            except IOError:
                return None

        return os.path.join(MEDIA_URL, thumb_file_name)
    return None
