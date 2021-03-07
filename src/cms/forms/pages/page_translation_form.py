import logging

from django.core.exceptions import ValidationError
from django.forms import TextInput
from django.utils.translation import ugettext_lazy as _

from ..custom_model_form import CustomModelForm
from ...constants import status
from ...models import PageTranslation
from ...utils.slug_utils import generate_unique_slug_helper


logger = logging.getLogger(__name__)


class PageTranslationForm(CustomModelForm):
    """
    Form for creating and modifying page translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = PageTranslation
        #: The fields of the model which should be handled by this form
        fields = ["title", "slug", "status", "text", "minor_edit"]
        widgets = {
            "slug": TextInput(attrs={"readonly": "readonly"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize Page translation form

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        """
        logger.info("New PageTranslationForm with args %s and kwargs %s", args, kwargs)

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop("region", None)
        self.language = kwargs.pop("language", None)
        disabled = kwargs.pop("disabled", None)

        # To set the status value through the submit button, we have to overwrite the field value for status.
        # We could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # Check if POST data was submitted
        if len(args) == 1:
            # Copy QueryDict because it is immutable
            post = args[0].copy()
            # Update the POST field with the status corresponding to the submitted button
            if "submit_draft" in args[0]:
                post.update({"status": status.DRAFT})
            elif "submit_review" in args[0]:
                post.update({"status": status.REVIEW})
            elif "submit_public" in args[0]:
                post.update({"status": status.PUBLIC})
            # Set the args to POST again
            args = (post,)
            logger.info("changed POST arg status manually")

        super().__init__(*args, **kwargs)

        # If form is disabled because the user has no permissions to edit the page, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The saved page translation object
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """

        logger.info(
            "PageTranslationForm saved with args %s, kwargs %s, cleaned data %s and changed data %s",
            args,
            kwargs,
            self.cleaned_data,
            self.changed_data,
        )

        # pop kwarg to make sure the super class does not get this param
        page = kwargs.pop("page", None)
        user = kwargs.pop("user", None)

        kwargs["commit"] = False  # Don't save yet. We just want the object.
        page_translation = super().save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when page translation is created
            page_translation.page = page
            page_translation.creator = user
            page_translation.language = self.language

        # Only create new version if content changed
        if not {"slug", "title", "text"}.isdisjoint(self.changed_data):
            page_translation.version = page_translation.version + 1
            page_translation.pk = None
        page_translation.save()

        return page_translation

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        return generate_unique_slug_helper(self, "page")

    def clean_text(self):
        """
        Validate the text field (see :ref:`overriding-modelform-clean-method`)

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content

        :return: The valid text
        :rtype: str
        """
        text = self.data["text"]

        if "<h1>" in text:
            raise ValidationError(
                _("Use of Heading 1 style not allowed."),
                code="no-heading-1",
            )

        return text
