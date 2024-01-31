"""
This module contains a list of Mime-Types that are allowed to be uploaded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Final

    from django.utils.functional import Promise


#: MIME type of PNG files
PNG: Final = "image/png"
#: MIME type of JPEG files
JPEG: Final = "image/jpeg"
#: MIME type of GIF files
GIF: Final = "image/gif"
#: MIME type of SVG files
SVG: Final = "image/svg+xml"
#: MIME type of PDF files
PDF: Final = "application/pdf"
#: MIME type of legacy 97-2007 Word files
DOC: Final = "application/msword"
#: MIME type of default Word files
DOCX: Final = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#: MIME type of legacy 97-2007 Excel files
XLS: Final = "application/vnd.ms-excel"
#: MIME type of default Excel files
XLSX: Final = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#: MIME type of legacy 97-2007 PowerPoint files
PPT: Final = "application/vnd.ms-powerpoint"
#: MIME type of default PowerPoint files
PPTX: Final = (
    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
)


#: MIME type of image files. Expand this list to add further data types.
IMAGES: Final[list[tuple[str, Promise]]] = [
    (PNG, _("PNG image")),
    (JPEG, _("JPEG image")),
]

#: MIME types of document files. Expand this list to add further data types.
DOCUMENTS: Final[list[tuple[str, Promise]]] = [
    (PDF, _("PDF document")),
]
#: Legacy MIME types that existed in the former Wordpress system.
LEGACY_TYPES: Final[list[tuple[str, Promise]]] = [
    (SVG, _("SVG image")),
    (GIF, _("GIF image")),
    (DOC, _("DOC document")),
    (DOCX, _("DOCX document")),
    (XLS, _("XLS document")),
    (XLSX, _("XLSX document")),
    (PPT, _("PPT document")),
    (XLSX, _("PPTX document")),
]

#: Allowed MIME types that can be uploaded.
UPLOAD_CHOICES: list[tuple[str, Promise]] = IMAGES + DOCUMENTS
#: Allowed MIME types that are allowed in the database.
CHOICES: Final[list[tuple[str, Promise]]] = UPLOAD_CHOICES + LEGACY_TYPES

if settings.LEGACY_FILE_UPLOAD:
    UPLOAD_CHOICES += LEGACY_TYPES
