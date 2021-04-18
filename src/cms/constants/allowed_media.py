"""
This module contains a list of Mime-Types that are allowed to be uploaded.
"""
from django.utils.translation import ugettext_lazy as _

#: MIME type of PNG files
PNG = "image/png"
#: MIME type of JPG files
JPG = "image/jpg"
#: MIME type of JPEG files
JPEG = "image/jpeg"
#: MIME type of PDF files
PDF = "application/pdf"

#: MIME type of image files. Expand this list to add further data types.
IMAGES = [
    (PNG, _("PNG image")),
    (JPG, _("JPG image")),
    (JPEG, _("JPEG image")),
]

#: MIME types of document files. Expand this list to add further data types.
DOCUMENTS = [(PDF, _("PDF document"))]

#: Allowed MIME types that can be uploaded.
CHOICES = IMAGES + DOCUMENTS
