from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from lxml.etree import LxmlError
from lxml.html import fragment_fromstring, tostring

from ..constants import status
from ..models import MediaFile
from ..utils import internal_link_utils
from ..utils.linkcheck_utils import fix_content_link_encoding
from ..utils.slug_utils import generate_unique_slug_helper
from .custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


class CustomContentModelForm(CustomModelForm):
    """
    Form for the content model forms for pages, events and POIs.
    """

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize custom content model form

        :param \**kwargs: The supplied keyword arguments
        """
        # Handle content edit lock
        self.changed_by_user = kwargs.pop("changed_by_user", None)
        self.locked_by_user = kwargs.pop("locked_by_user", None)

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        # Always set the minor edit and the automatic translation to unchecked
        # to make sure it does not influence future versions (unless manually enabled)
        self.initial["minor_edit"] = False
        self.initial["automatic_translation"] = False

        # The slug is not required because it will be auto-generated if left blank
        if "slug" in self.fields:
            self.fields["slug"].required = False

        if not self.locked_by_user:
            try:
                self.locked_by_user = self.instance.foreign_object.get_locking_user()
            except ObjectDoesNotExist:
                # If the foreign object does not exist yet, there ist also no lock so nothing must be done
                pass

    def clean(self) -> dict[str, Any]:
        """
        This method extends the ``clean()``-method to verify that a user can modify this content model

        :return: The cleaned data (see :ref:`overriding-modelform-clean-method`)
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

        if cleaned_data.get("automatic_translation") and cleaned_data.get("minor_edit"):
            self.add_error(
                None,
                forms.ValidationError(
                    _(
                        'The options "automatic translation" and "minor edit" are mutually exclusive.'
                    ),
                    code="invalid",
                ),
            )

        return cleaned_data

    # pylint: disable=too-many-branches
    def clean_content(self) -> str:
        """
        Validate the content field (see :ref:`overriding-modelform-clean-method`) and applies changes
        to ``<img>``- and ``<a>``-Tags to match the guidelines.

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content

        :return: The valid content
        """
        try:
            # this returns <div><p>...</p></div> when passed <p>...</p>
            content = fragment_fromstring(self.cleaned_data["content"])
        except LxmlError:
            # The content is not guaranteed to be valid html, for example it may be empty
            return self.cleaned_data["content"]

        # Convert heading 1 to heading 2
        for heading in content.iter("h1"):
            heading.tag = "h2"
            self.logger.debug(
                "Replaced heading 1 with heading 2: %r",
                tostring(heading, encoding="unicode"),
            )

        # Convert pre and code tags to p tags
        for monospaced in content.iter("pre", "code"):
            tag_type = monospaced.tag
            monospaced.tag = "p"
            self.logger.debug(
                "Replaced %r tag with p tag: %r",
                tag_type,
                tostring(monospaced, encoding="unicode"),
            )

        # Set link-external as class for external links
        for link in content.iter("a"):
            if href := link.get("href"):
                is_external = not any(url in href for url in settings.INTERNAL_URLS)
                if "link-external" not in link.classes and is_external:
                    link.classes.add("link-external")
                    self.logger.debug(
                        "Added class 'link-external' to %r",
                        tostring(link, encoding="unicode"),
                    )
                elif "link-external" in link.classes and not is_external:
                    link.classes.remove("link-external")
                    self.logger.debug(
                        "Removed class 'link-external' from %r",
                        tostring(link, encoding="unicode"),
                    )

        # Remove external links
        for link in content.iter("a"):
            link.attrib.pop("target", None)
            self.logger.debug(
                "Removed target attribute from link: %r",
                tostring(link, encoding="unicode"),
            )

        # Update internal links
        for link in content.iter("a"):
            if href := link.attrib.get("href"):
                if translation := internal_link_utils.update_link_language(
                    href, link.text, self.instance.language.slug
                ):
                    translated_url, translated_text = translation
                    link.set("href", translated_url)
                    # translated_text might be None if the link tag consists of other tags instead of plain text
                    if translated_text:
                        link.text = translated_text
                    self.logger.debug(
                        "Updated link url from %s to %s", href, translated_url
                    )

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

        content_str = tostring(content, encoding="unicode", with_tail=False)
        return fix_content_link_encoding(content_str)

    def clean_slug(self) -> str:
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        """
        unique_slug = generate_unique_slug_helper(
            self, self._meta.model.foreign_field()
        )
        self.data = self.data.copy()
        self.data["slug"] = unique_slug
        return unique_slug

    def save(self, commit: bool = True, foreign_form_changed: bool = False) -> Any:
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :param foreign_form_changed: Whether or not the foreign form of this translation form was changed
        :return: The saved content translation object
        """

        if commit:
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

    def add_success_message(self, request: HttpRequest) -> None:
        """
        This adds a success message for a translation form.
        Requires the attributes "title", "status" and "foreign_object" on the form instance.

        :param request: The current request submitting the translation form
        """
        status_messages = {
            status.AUTO_SAVE: _('{} "{}" was saved automatically'),
            status.REVIEW: _('{} "{}" was successfully submitted for review'),
            status.DRAFT: _('{} "{}" was successfully saved as draft'),
            status.PUBLIC: (
                _('{} "{}" was successfully published')
                if "status" in self.changed_data
                else _('{} "{}" was successfully updated')
            ),
        }

        model_name = type(self.instance.foreign_object)._meta.verbose_name.title()
        if message := status_messages.get(self.instance.status):
            messages.success(request, message.format(model_name, self.instance.title))

    class Meta:
        fields = [
            "title",
            "status",
            "content",
            "minor_edit",
            "automatic_translation",
            "machine_translated",
        ]
