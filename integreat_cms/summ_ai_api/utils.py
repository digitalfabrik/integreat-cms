"""
This module contains helpers for the SUMM.AI API client
"""
import logging
import itertools

from html import unescape

from lxml.etree import SubElement, strip_tags
from lxml.html import fromstring, tostring

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _

from ..cms.constants import status
from ..cms.utils.translation_utils import gettext_many_lazy as __

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class TextField:
    """
    A class for simple text fields
    """

    #: The name of the corresponding model field
    #:
    #: :type: str
    name = ""
    #: The source text
    #:
    #: :type: str
    text = ""
    #: The translated text
    #:
    #: :type: str
    translated_text = ""
    #: The exception which occurred during translation, if any
    #:
    #: :type: Exception
    exception = None

    def __init__(self, name, translation):
        """
        Constructor initializes the class variables

        :param text: The text to be translated
        :type text: str
        """
        self.name = name
        self.text = getattr(translation, name, "").strip()

    def translate(self, translated_text):
        """
        Translate the text of the current text field

        :param translated_text: The translated text
        :type translated_text: str
        """
        self.translated_text = translated_text

    def __repr__(self):
        """
        The representation used for logging

        :return: The canonical string representation of the text field
        :rtype: str
        """
        return f"<{type(self).__name__} (text: {self.text})>"


# pylint: disable=too-few-public-methods
class HTMLSegment(TextField):
    """
    A class for translatable HTML segments
    """

    #: The current HTML segment
    #:
    #: :type: lxml.html.HtmlElement
    segment = None

    # pylint: disable=super-init-not-called
    def __init__(self, segment):
        """
        Convert the lxml tree element to a flat text string.
        Preserve <br> tags as new lines characters.
        Remove all inner tags but keep their text content.
        Unescape all special HTML entities into unicode characters.

        :param segment: The current HTML segment
        :type segment: ~integreat_cms.cms.models.regions.region.Region
        """
        self.segment = segment
        # Preserve new line tags
        for br in self.segment.iter("br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        # Strip all inner tags
        strip_tags(self.segment, "*")
        # Unescape to convert umlauts etc. to unicode
        self.text = unescape(self.segment.text_content()).strip()

    def translate(self, translated_text):
        """
        Translate the current HTML segment and create new sub elements for line breaks

        :param translated_text: The translated text
        :type translated_text: str
        """
        # Only do something if response was not empty (otherwise keep original text)
        if translated_text:
            # Split the text by newlines characters
            lines = translated_text.splitlines()
            # Take the first line as initial text
            self.segment.text = lines[0]
            # If there are more than one line returned, insert <br> tags
            for line in lines[1:]:
                SubElement(self.segment, "br").tail = line


# pylint: disable=too-few-public-methods
class HTMLField:
    """
    A class for more complex HTML fields which are splitted into segments
    """

    #: The name of the corresponding model field
    #:
    #: :type: str
    name = ""
    #: The list of HTML segments
    #:
    #: :type: list [ lxml.html.HtmlElement ]
    segments = []
    #: The current HTML stream
    #:
    #: :type: lxml.html.HtmlElement
    html = None

    def __init__(self, name, translation):
        """
        Parse the HTML string into an lxml tree object and split into segments

        :param html: The HTML string content of this field
        :type html: str
        """
        self.name = name
        if html_str := getattr(translation, name, ""):
            self.html = fromstring(html_str)
            # Translate all specified tags (and filter out empty segments)
            self.segments = [
                HTMLSegment(segment=segment)
                for segment in self.html.iter(*settings.SUMM_AI_HTML_TAGS)
            ]

    def __repr__(self):
        """
        The representation used for logging

        :return: The canonical string representation of the HTML field
        :rtype: str
        """
        return f"<HTMLField (segments: {self.segments})>"

    @property
    def translated_text(self):
        """
        Assemble the content of the HTML segments into a HTML string again

        :returns: The translated HTML
        :rtype: str
        """
        if self.html is not None:
            return tostring(
                self.html, encoding="unicode", method="html", pretty_print=True
            )
        return None

    @property
    def exception(self):
        """
        Check if any of the segments experienced an error

        :returns: The first exception of this HTML field
        :rtype: Exception
        """
        return next(
            (segment.exception for segment in self.segments if segment.exception), None
        )


# pylint: disable=too-many-instance-attributes
class TranslationHelper:
    """
    Custom helper class for interaction with SUMM.AI
    """

    #: The current request
    #:
    #: :type: ~django.http.HttpRequest
    request = None
    #: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
    #: subclass of the current content type
    #:
    #: :type: ~django.forms.models.ModelFormMetaclass
    form_class = None
    #: The current object instance to be translated
    #:
    #: :type: ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel
    object_instance = None
    #: The German source translation of the object instance
    #:
    #: :type: ~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation
    german_translation = None
    #: Wether or not the translation was successful
    #:
    #: :type: bool
    valid = True
    #: list: The text fields of this helper
    #:
    #: :type: list
    text_fields = []
    #: The HTML fields of this helper
    #:
    #: :type: list
    html_fields = []

    def __init__(self, request, form_class, object_instance):
        """
        Constructor initializes the class variables

        :param request: current request
        :type request: ~django.http.HttpRequest

        :param form_class: The :class:`~integreat_cms.cms.forms.custom_content_model_form.CustomContentModelForm`
                           subclass of the current content type
        :type form_class: :type: ~django.forms.models.ModelFormMetaclass

        :param object_instance: The current object instance
        :type object_instance: ~integreat_cms.cms.models.abstract_content_model.AbstractContentModel
        """
        self.request = request
        self.form_class = form_class
        self.object_instance = object_instance
        self.german_translation = object_instance.get_translation(
            settings.SUMM_AI_GERMAN_LANGUAGE_SLUG
        )
        if not self.german_translation:
            messages.error(
                self.request,
                _('No German translation could be found for {} "{}".').format(
                    type(object_instance)._meta.verbose_name.title(),
                    object_instance.best_translation.title,
                ),
            )
            self.valid = False
            return
        self.text_fields = [
            TextField(name=text_field, translation=self.german_translation)
            for text_field in settings.SUMM_AI_TEXT_FIELDS
        ]
        self.html_fields = [
            HTMLField(name=html_field, translation=self.german_translation)
            for html_field in settings.SUMM_AI_HTML_FIELDS
        ]

    @property
    def fields(self):
        """
        Get all fields of this helper instance

        :returns: All fields which need to be translated
        :rtype: list [ ~integreat_cms.summ_ai_api.utils.TextField or ~integreat_cms.summ_ai_api.utils.HTMLField ]
        """
        return self.text_fields + self.html_fields

    def get_text_fields(self):
        """
        Get all text fields of this helper instance
        (all native :attr:`~integreat_cms.summ_ai_api.utils.TranslationHelper.text_fields`
        combined with all segments of all
        :attr:`~integreat_cms.summ_ai_api.utils.TranslationHelper.html_fields`)

        :returns: All text fields and segments which need to be translated
        :rtype: list [ ~integreat_cms.summ_ai_api.utils.TextField ]
        """
        if not self.valid:
            return []
        text_fields = list(
            filter(
                # Filter out empty texts
                lambda x: x.text,
                itertools.chain(
                    # Get all plain text fields
                    self.text_fields,
                    # Get all segments of all HTML fields
                    *[html_field.segments for html_field in self.html_fields],
                ),
            )
        )
        logger.debug(
            "Text fields for %r: %r",
            self,
            text_fields,
        )
        return text_fields

    def commit(self, easy_german):
        """
        Save the translated changes to the database

        :param easy_german: The language object of Easy German
        :type easy_german: ~integreat_cms.cms.models.languages.language.Language
        """
        if not self.valid:
            return
        # Check whether any of the fields returned an error
        if any(field.exception for field in self.fields):
            messages.error(
                self.request,
                __(
                    _(
                        '{} "{}" could not be automatically translated into Easy German.'
                    ).format(
                        type(self.object_instance)._meta.verbose_name.title(),
                        self.german_translation.title,
                    ),
                    _("Please try again later or contact an administrator"),
                ),
            )
            return
        # Initialize form to create new translation object
        content_translation_form = self.form_class(
            data={
                # Pass all inherited fields
                **{
                    field_name: getattr(self.german_translation, field_name, "")
                    for field_name in settings.SUMM_AI_INHERITED_FIELDS
                },
                # Pass all translated texts as data values
                **{field.name: field.translated_text for field in self.fields},
                # Always set automatic translations into pending review state
                "status": status.REVIEW,
            },
            instance=self.object_instance.get_translation(
                settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
            ),
            additional_instance_attributes={
                "creator": self.request.user,
                "language": easy_german,
                self.german_translation.foreign_field(): self.object_instance,
            },
        )
        # Validate translation form
        if not content_translation_form.is_valid():
            logger.error(
                "Automatic translation into Easy German for %r could not be created because of %s",
                self.object_instance,
                content_translation_form.errors,
            )
            messages.error(
                self.request,
                _(
                    '{} "{}" could not be automatically translated into Easy German.'
                ).format(
                    type(self.object_instance)._meta.verbose_name.title(),
                    self.german_translation.title,
                ),
            )
            return
        # Save new translation
        content_translation_form.save()
        logger.debug(
            "Successfully translated %r into Easy German",
            content_translation_form.instance,
        )
        messages.success(
            self.request,
            _('{} "{}" has been successfully translated into Easy German.').format(
                type(self.object_instance)._meta.verbose_name.title(),
                self.german_translation.title,
            ),
        )

    def __repr__(self):
        """
        The representation used for logging

        :return: The canonical string representation of the translation helper
        :rtype: str
        """
        return f"<TranslationHelper (translation: {self.german_translation!r})>"
