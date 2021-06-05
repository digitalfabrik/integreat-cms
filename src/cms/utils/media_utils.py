"""
Utility functions for the media management. Most of the functions are used to transform media data to other data types.
"""
import logging
import math
import os

from PIL import Image

from ..models import MediaFile

logger = logging.getLogger(__name__)

# pylint: disable=too-many-locals
def generate_thumbnail(original_image, width, height, crop):
    """
    Creates a thumbnail for a given media_file.

    :param original_image: Original image for the thumbnail
    :type original_image: django.core.files.uploadedfile.InMemoryUploadedFile

    :param width: Width of the desired thumbnail
    :type width: int

    :param height: Height of the desired thumbnail
    :type height: int

    :param crop: Option to either crop the thumbnail or not.
    :type crop: bool

    :return: The physical path to the created thumbnail.
    :rtype: str
    """
    logger.debug(
        "Generating thumbnail for %r with size: %sx%s%s",
        original_image,
        width,
        height,
        " (cropped)" if crop else "",
    )
    # Split original filename into name and extension
    name, extension = os.path.splitext(original_image.name)
    # Generate a valid filename for this field
    thumbnail_filename = MediaFile.thumbnail.field.generate_filename(
        None, f"{name}_thumbnail{extension}"
    )
    # Make filename unique
    thumbnail_filename = MediaFile.thumbnail.field.storage.get_available_name(
        thumbnail_filename
    )
    # Get absolute file path
    thumbnail_path = MediaFile.thumbnail.field.storage.path(thumbnail_filename)
    logger.debug(
        "Thumbnail path: %r",
        thumbnail_path,
    )

    try:
        image = Image.open(original_image)
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
        # Make sure directory of thumbnail exists
        directory = os.path.dirname(thumbnail_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print("created")
        with open(thumbnail_path, "w+b") as thumbnail_file:
            thumbnail.save(thumbnail_file, image.format)
        return thumbnail_filename
    except IOError as e:
        logger.error("Thumbnail generation for %r failed", original_image)
        logger.exception(e)
    return None
