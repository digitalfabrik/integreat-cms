"""
Utility functions for the media management. Most of the functions are used to transform media data to other data types.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, TYPE_CHECKING

import cairosvg
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connection
from PIL import Image, ImageOps

from integreat_cms.cms.models.media.media_file import Directory, MediaFile

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
        if original_image.content_type == "image/svg+xml":
            original_image.seek(0)
            svg_bytes = original_image.read()
            png_bytes = cairosvg.svg2png(
                bytestring=svg_bytes, output_width=size, output_height=size
            )
            image = Image.open(BytesIO(png_bytes))
        else:
            image = Image.open(original_image)

        # Save format, as this information will be lost when resizing the image
        image_format = image.format
        if TYPE_CHECKING:
            assert image_format
        if crop:
            # Get minimum of original size of the image because ImageOps.fit would otherwise increase the image size
            size = min(image.width, image.height, size)
            # Resize and crop the image into a square of at most the specified size.
            image = ImageOps.fit(image, (size, size), method=Image.LANCZOS)  # type: ignore[attr-defined,assignment]
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
    except OSError:
        logger.exception("Thumbnail generation for %r failed", original_image)
        return None
    else:
        return thumbnail


def get_mixed_tree_paths() -> dict[str, Any]:
    """
    Recursively builds paths for both Directory and MediaFile objects.
    The CTE will first build paths for directories and then attach MediaFile objects.
    """
    # Get the table names dynamically
    directory_table = Directory._meta.db_table
    mediafile_table = MediaFile._meta.db_table

    # ruff: noqa: S608
    with connection.cursor() as cursor:
        # TODO @PeterNerlich: We kind of have entirely disjoint trees, one for each region + global
        #   this is still missing from this and needs to be addressed when finishing this.
        #  If you're wondering what happens when a region has a directory with the same name
        #   as one in the global library: Simply both are shown, separately, with the same name.
        cursor.execute(f"""
            WITH RECURSIVE directory_tree(id, name, parent_id, full_path, is_directory) AS (
                -- Base case: Select root directories (parent_id IS NULL)
                SELECT id, name, parent_id, name::TEXT AS full_path, TRUE
                FROM {directory_table}
                WHERE parent_id IS NULL
                UNION ALL
                -- Recursive case: Join directories and their subdirectories (children)
                SELECT d.id, d.name, d.parent_id, (dt.full_path || '/' || d.name)::TEXT, TRUE
                FROM {directory_table} d
                JOIN directory_tree dt ON d.parent_id = dt.id
            ),
            mediafile_tree AS (
                -- MediaFile case: Attach MediaFile objects to the full path of the parent directory
                SELECT mf.id, mf.name, mf.parent_directory_id AS parent_id, (dt.full_path || '/' || mf.name)::TEXT AS full_path, FALSE AS is_directory
                FROM {mediafile_table} mf
                JOIN directory_tree dt ON mf.parent_directory_id = dt.id
            )
            -- Combine the results from both directories and media files
            SELECT id, full_path, is_directory FROM directory_tree
            UNION ALL
            SELECT id, full_path, is_directory FROM mediafile_tree;
        """)
        rows = cursor.fetchall()
        return {row[1]: {"id": row[0], "is_directory": row[2]} for row in rows}
