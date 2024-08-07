"""
Utility functions for the media management. Most of the functions are used to transform media data to other data types.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def generate_thumbnail(
    original_image: InMemoryUploadedFile,
    size: int = settings.MEDIA_THUMBNAIL_SIZE,
    crop: bool = settings.MEDIA_THUMBNAIL_CROP,
) -> InMemoryUploadedFile | None:
    """
    Creates a thumbnail for a given media_file.

    :param original_image: Original image for the thumbnail
    :param size: Desired size of the thumbnail (maximum for height and with), defaults to
                 :attr:`~integreat_cms.core.settings.MEDIA_THUMBNAIL_SIZE`
    :param crop: Whether the thumbnail should be cropped (resulting in a square regardless of the initial aspect ratio),
                 defaults to :attr:`~integreat_cms.core.settings.MEDIA_THUMBNAIL_CROP`
    :return: The created thumbnail in memory
    """
    logger.debug(
        "Generating thumbnail for %r with max size: %spx%s",
        original_image,
        size,
        " (cropped)" if crop else "",
    )
    try:
        image = Image.open(original_image)
        # Save format, as this information will be lost when resizing the image
        image_format = image.format
        if TYPE_CHECKING:
            assert image_format
        if crop:
            # Get minimum of original size of the image because ImageOps.fit would otherwise increase the image size
            size = min(image.width, image.height, size)
            # Resize and crop the image into a square of at most the specified size.
            image = ImageOps.fit(image, (size, size), method=Image.LANCZOS)  # type: ignore[attr-defined]
        else:
            # Resize the image so that the longer side is at most the specified size
            image.thumbnail((size, size), resample=Image.LANCZOS)  # type: ignore[attr-defined]
        # Write PIL image to BytesIO buffer
        buffer = BytesIO()
        # Use optimize option to reduce the image size. Higher quality parameter reduces compression
        image.save(buffer, format=image_format, optimize=True, quality=65)
        # Construct InMemoryUploadedFile from buffer
        thumbnail = InMemoryUploadedFile(
            file=buffer,
            field_name="thumbnail",
            name=original_image.name,
            content_type=Image.MIME[image_format],
            size=buffer.tell(),
            charset=None,
        )
        logger.debug("Successfully generated thumbnail %r", thumbnail)
        return thumbnail
    except IOError as e:
        logger.error("Thumbnail generation for %r failed", original_image)
        logger.exception(e)
    return None
