from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from ...models import OfferTemplate
from ...utils.slug_utils import generate_unique_slug_helper
from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any


class OfferTemplateForm(CustomModelForm):
    """
    Form for creating and modifying offer template objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = OfferTemplate
        #: The fields of the model which should be handled by this form
        fields = [
            "name",
            "slug",
            "thumbnail",
            "url",
            "post_data",
            "use_postal_code",
            "supported_by_app_in_content",
            "is_zammad_form",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize offer template form

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        super().__init__(*args, **kwargs)

        self.fields["slug"].required = False

    def clean(self) -> dict:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()
        if not cleaned_data["is_zammad_form"] and not cleaned_data["url"]:
            self.add_error("url", _("This field is required."))
        if not cleaned_data["is_zammad_form"] and not cleaned_data["thumbnail"]:
            self.add_error("thumbnail", _("This field is required."))
        return cleaned_data

    def clean_slug(self) -> str:
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        """
        return generate_unique_slug_helper(self, "offer-template")

    def clean_post_data(self) -> dict:
        """
        Validate the post data field (see :ref:`overriding-modelform-clean-method`)

        :return: The valid post data
        """
        if cleaned_post_data := self.cleaned_data["post_data"]:
            return cleaned_post_data
        return {}
