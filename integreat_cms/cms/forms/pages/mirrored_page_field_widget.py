from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.urls import reverse

if TYPE_CHECKING:
    from .page_form import PageForm


class MirroredPageFieldWidget(forms.widgets.Select):
    """
    This Widget class is used to append the url for retrieving the preview of the mirrored page to the data attributes of the options
    """

    #: The form this field is bound to
    form: PageForm | None = None
    #: The current language slug
    language_slug: str | None = None

    # pylint: disable=too-many-arguments
    def create_option(
        self,
        name: str,
        value: int,
        label: str,
        selected: bool,
        index: int,
        subindex: int | None = None,
        attrs: dict | None = None,
    ) -> dict:
        """
        This function creates an option which can be selected in the parent field

        :param name: The name of the option
        :param value: the value of the option (the page id)
        :param label: The label of the option
        :param selected: Whether or not the option is selected
        :param index: The index of the option
        :param subindex: The subindex of the option
        :param attrs: The attributes of the option
        :return: The option dict
        """
        if TYPE_CHECKING:
            assert self.form
            assert self.form.instance
            assert self.form.instance.region

        # Create dictionary of options
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        preview_url = reverse(
            "get_page_content_ajax",
            kwargs={
                "region_slug": self.form.instance.region.slug,
                "language_slug": self.language_slug,
                "page_id": value,
            },
        )
        option_dict["attrs"]["data-preview-url"] = preview_url
        return option_dict
