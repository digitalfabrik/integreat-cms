from urllib.parse import urlparse

from lxml.etree import LxmlError
from lxml.html import fromstring, tostring

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from ..utils.slug_utils import generate_unique_slug_helper
from ..constants import status
from ..models import MediaFile
from .custom_model_form import CustomModelForm


class CustomContentModelForm(CustomModelForm):
    """
    Form for the content model forms for pages, events and POIs.
    """

    def __init__(self, **kwargs):
        r"""
        Initialize custom content model form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        # Pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop("region", None)
        self.language = kwargs.pop("language", None)

        # Handle content edit lock
        self.changed_by_user = kwargs.pop("changed_by_user", None)
        self.locked_by_user = kwargs.pop("locked_by_user", None)

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # Always set the minor edit to unchecked to make sure it does not influence future versions
        # (unless manually enabled)
        self.initial["minor_edit"] = False

        # The slug is not required because it will be auto-generated if left blank
        if "slug" in self.fields:
            self.fields["slug"].required = False

        if not self.locked_by_user:
            try:
                self.locked_by_user = self.instance.foreign_object.get_locking_user()
            except ObjectDoesNotExist:
                # If the foreign object does not exist yet, there ist also no lock so nothing must be done
                pass

    def clean(self):
        """
        This method extends the ``clean()``-method to verify that a user can modify this content model

        :return: The cleaned data (see :ref:`overriding-modelform-clean-method`)
        :rtype: dict
        """
        # Validate CustomModelForm
        cleaned_data = super().clean()

        force_update = cleaned_data.get("status") == status.AUTO_SAVE
        if (
            not force_update
            and self.changed_by_user
            and self.locked_by_user
            and self.changed_by_user != self.locked_by_user
        ):
            self.add_error(
                None,
                forms.ValidationError(
                    _(
                        "Could not update because this content because it is already being edited by another user"
                    ),
                    code="invalid",
                ),
            )

        return cleaned_data

    def clean_content(self):
        """
        Validate the content field (see :ref:`overriding-modelform-clean-method`) and applies changes
        to ``<img>``- and ``<a>``-Tags to match the guidelines.

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content

        :return: The valid content
        :rtype: str
        """
        try:
            content = fromstring(self.cleaned_data["content"])
        except LxmlError:
            # The content is not guaranteed to be valid html, for example it may be empty
            return self.cleaned_data["content"]

        # Convert heading 1 to heading 2
        for heading in content.iter("h1"):
            heading.tag = "h2"
            self.logger.debug(
                "Replaced heading 1 with heading 2: %r", tostring(heading)
            )

        # Convert pre and code tags to p tags
        for monospaced in content.iter("pre", "code"):
            tag_type = monospaced.tag
            monospaced.tag = "p"
            self.logger.debug(
                "Replaced %r tag with p tag: %r", tag_type, tostring(monospaced)
            )

        # Remove external links
        for link in content.iter("a"):
            link.attrib.pop("target", None)
            self.logger.debug("Removed target attribute from link: %r", tostring(link))

        # Scan for media files in content and replace alt texts
        for image in content.iter("img"):
            self.logger.debug(
                "Image tag found in content (src: %s)", image.attrib["src"]
            )
            # Remove host
            relative_url = urlparse(image.attrib["src"]).path
            # Remove media url prefix if exists
            if relative_url.startswith(settings.MEDIA_URL):
                relative_url = relative_url[len(settings.MEDIA_URL) :]
            # Check whether media file exists in database
            media_file = MediaFile.objects.filter(
                Q(file=relative_url) | Q(thumbnail=relative_url)
            ).first()
            # Replace alternative text
            if media_file and media_file.alt_text:
                self.logger.debug("Image alt text replaced: %r", media_file.alt_text)
                image.attrib["alt"] = media_file.alt_text

        return tostring(content, with_tail=False).decode("utf-8")

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        unique_slug = generate_unique_slug_helper(
            self, self._meta.model.foreign_field()
        )
        self.data = self.data.copy()
        self.data["slug"] = unique_slug
        return unique_slug

    # pylint: disable=arguments-differ
    def save(self, commit=True, foreign_form_changed=False):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :param foreign_form_changed: Whether or not the foreign form of this translation form was changed
        :type foreign_form_changed: bool

        :return: The saved page translation object
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """

        # Delete now outdated link objects
        self.instance.links.all().delete()

        # If none of the text content fields were changed, but the foreign form was, treat as minor edit (even if checkbox isn't clicked)
        if {"title", "content"}.isdisjoint(self.changed_data) and foreign_form_changed:
            self.logger.debug("Set 'minor_edit=True' since the content did not change")
            self.instance.minor_edit = True

        # Save new version
        self.instance.version += 1
        self.instance.pk = None

        # Save CustomModelForm
        return super().save(commit=commit)

    def add_success_message(self, request):
        """
        This adds a success message for a translation form.
        Requires the attributes "title", "status" and "foreign_object" on the form instance.

        :param request: The current request submitting the translation form
        :type request: ~django.http.HttpRequest
        """
        model_name = type(self.instance.foreign_object)._meta.verbose_name.title()
        if not self.instance.status == status.PUBLIC:
            messages.success(
                request,
                _('{} "{}" was successfully saved as draft').format(
                    model_name, self.instance.title
                ),
            )
        elif "status" not in self.changed_data:
            messages.success(
                request,
                _('{} "{}" was successfully updated').format(
                    model_name, self.instance.title
                ),
            )
        else:
            messages.success(
                request,
                _('{} "{}" was successfully published').format(
                    model_name, self.instance.title
                ),
            )
