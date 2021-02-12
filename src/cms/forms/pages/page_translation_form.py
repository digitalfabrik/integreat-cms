import logging
import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from ...constants import status
from ...models import PageTranslation
from ...utils.slug_utils import generate_unique_slug


logger = logging.getLogger(__name__)


class PageTranslationForm(forms.ModelForm):
    """
    Form for creating and modifying page translation objects
    """

    class Meta:
        model = PageTranslation
        fields = ["title", "slug", "status", "text", "minor_edit"]

    def __init__(self, *args, **kwargs):

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
        return generate_unique_slug(self, "page")

    def clean_text(self):
        text = self.data["text"]

        if "<h1>" in text:
            raise ValidationError(
                _("Use of Heading 1 style is not allowed."),
                code="no-heading-1",
            )

    def clean_text2(self):
        text = self.data["text"]

        # r'href=[\'"]?([^\'" >]+)'
        # r(?<=href=").*?(?=")+.*?(?<=target=")
        r = re.compile(r"(\B|\b)<a+.+\/a>(\B|\b)")
        urls = r.findall(text)
        if urls:
            # print(urls)
            raise ValidationError(
                _("Use of external links is not allowed!"),
                code="no-external-links",
            )
        else:
            print("No external links found.")

        return text
