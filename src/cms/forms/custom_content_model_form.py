import logging

from urllib.parse import urlparse

from lxml.html import fromstring, tostring

from django.db.models import Q

from backend.settings import MEDIA_URL
from ..models import MediaFile
from .custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class CustomContentModelForm(CustomModelForm):
    """
    Form for the content model forms for pages, events and POIs.
    """

    def content_clean_method(self, field_name):
        """
        Validate the content (text/description) field (see :ref:`overriding-modelform-clean-method`) and applies changes
        to ``<img>``- and ``<a>``-Tags to match the guidelines.

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content

        :return: The valid content
        :rtype: str
        """
        content = fromstring(self.cleaned_data[field_name])

        # Convert heading 1 to heading 2
        for heading in content.iter("h1"):
            heading.tag = "h2"
            logger.debug("Replaced heading 1 with heading 2: %r", tostring(heading))

        # Remove external links
        for link in content.iter("a"):
            link.attrib.pop("target", None)
            logger.debug("Removed target attribute from link: %r", tostring(link))

        # Scan for media files in content and replace alt texts
        for image in content.iter("img"):
            logger.debug("Image tag found in content (src: %s)", image.attrib["src"])
            # Remove host
            relative_url = urlparse(image.attrib["src"]).path
            # Remove media url prefix if exists
            if relative_url.startswith(MEDIA_URL):
                relative_url = relative_url[len(MEDIA_URL) :]
            # Check whether media file exists in database
            media_file = MediaFile.objects.filter(
                Q(file=relative_url) | Q(thumbnail=relative_url)
            ).first()
            # Replace alternative text
            if media_file and media_file.alt_text:
                logger.debug("Image alt text replaced: %r", media_file.alt_text)
                image.attrib["alt"] = media_file.alt_text

        return tostring(content, with_tail=False, pretty_print=True).decode("utf-8")
