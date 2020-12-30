import logging

from django import forms

from ...models import ImprintPage


logger = logging.getLogger(__name__)


class ImprintForm(forms.ModelForm):
    """
    Form for creating and modifying imprint objects
    """

    class Meta:
        model = ImprintPage
        fields = ["icon"]

    def __init__(self, *args, **kwargs):

        logger.info(
            "New ImprintForm instantiated with args %s and kwargs %s", args, kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        self.region = kwargs.pop("region", None)
        disabled = kwargs.pop("disabled", None)

        # instantiate ModelForm
        super().__init__(*args, **kwargs)

        # If form is disabled because the user has no permissions to manage the imprint, disable all form fields
        if disabled:
            for _, field in self.fields.items():
                field.disabled = True

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):

        logger.debug(
            "ImprintForm saved with args %s, kwargs %s, cleaned data %s and changed data %s",
            args,
            kwargs,
            self.cleaned_data,
            self.changed_data,
        )

        # don't commit saving of ModelForm, because required fields are still missing
        kwargs["commit"] = False
        imprint = super().save(*args, **kwargs)

        if not self.instance.id:
            # only update these values when imprint is created
            imprint.region = self.region
        imprint.save()
        return imprint
