"""
This module contains a list of Mime-Types that are allowed to be uploaded.
"""
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

#: MIME type of PNG files
PNG = "image/png"
#: MIME type of JPEG files
JPEG = "image/jpeg"
#: MIME type of GIF files
GIF = "image/gif"
#: MIME type of SVG files
SVG = "image/svg+xml"
#: MIME type of PDF files
PDF = "application/pdf"
#: MIME type of legacy 97-2007 Word files
DOC = "application/msword"
#: MIME type of default Word files
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#: MIME type of legacy 97-2007 Excel files
XLS = "application/vnd.ms-excel"
#: MIME type of default Excel files
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#: MIME type of legacy 97-2007 PowerPoint files
PPT = "application/vnd.ms-powerpoint"
#: MIME type of default PowerPoint files
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


#: MIME type of image files. Expand this list to add further data types.
IMAGES = [
    (PNG, _("PNG image")),
    (JPEG, _("JPEG image")),
]

#: MIME types of document files. Expand this list to add further data types.
DOCUMENTS = [
    (PDF, _("PDF document")),
]
#: Legacy MIME types that existed in the former Wordpress system.
LEGACY_TYPES = [
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
UPLOAD_CHOICES = IMAGES + DOCUMENTS
#: Allowed MIME types that are allowed in the database.
CHOICES = UPLOAD_CHOICES + LEGACY_TYPES

if settings.LEGACY_FILE_UPLOAD:
    UPLOAD_CHOICES += LEGACY_TYPES
