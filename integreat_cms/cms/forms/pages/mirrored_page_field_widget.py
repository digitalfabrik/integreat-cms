from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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

    mirrored_page_region_slug: str | None = None

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
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        preview_url = reverse(
            "get_page_content_ajax",
            kwargs={
                "region_slug": self.mirrored_page_region_slug,
                "language_slug": self.language_slug,
                "page_id": value,
            },
        )
        option_dict["attrs"]["data-preview-url"] = preview_url

        # Keep the currently selected mirrored page visible but disabled if it no longer
        # has a public translation in the default language
        instance = self.form.instance if self.form else None
        default_language = instance.region.default_language
        if (
            instance
            and str(instance.mirrored_page_id) == str(value)
            and default_language
            and not instance.mirrored_page.get_public_translation(default_language.slug)
        ):
            option_dict["attrs"]["disabled"] = True
            option_dict["attrs"]["title"] = _(
                "The page currently selected as live content is not visible to users at this time because it is in draft status. Once the page is published, the content will be visible again."
            )

        return option_dict
