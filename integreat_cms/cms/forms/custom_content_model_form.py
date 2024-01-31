from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from ..constants import status
from ..utils.content_translation_utils import get_cleaned_content, update_links_to
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

    def clean_content(self) -> str:
        """
        Validate the content field (see :ref:`overriding-modelform-clean-method`) and applies changes
        to ``<img>``- and ``<a>``-Tags to match the guidelines.

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content

        :return: The valid content
        """
        return get_cleaned_content(
            self.cleaned_data["content"], self.instance.language.slug
        )

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
        result = super().save(commit=commit)

        # Update links to this content translation
        # Also update if the status got changed, since title or slug might have changed in a previous draft version
        if (
            commit
            and self.instance.status == status.PUBLIC
            and not {"title", "slug", "status"}.isdisjoint(self.changed_data)
        ):
            update_links_to(self.instance, self.instance.creator)

        return result

    def add_success_message(self, request: HttpRequest) -> None:
        """
        This adds a success message for a translation form.
        Requires the attributes "title", "status" and "foreign_object" on the form instance.

        :param request: The current request submitting the translation form
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

    class Meta:
        fields = [
            "title",
            "status",
            "content",
            "minor_edit",
            "automatic_translation",
            "machine_translated",
        ]
