from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.urls import reverse

if TYPE_CHECKING:
    from typing import Any

    from django.utils.safestring import SafeString


class ParentFieldWidget(forms.widgets.Select):
    """
    This Widget class is used to append the url for retrieving the page order tables to the data attributes of the options
    """

    #: The form this field is bound to
    form = None

    # pylint: disable=too-many-arguments
    def create_option(
        self,
        name: str,
        value: int | str,
        label: SafeString | str,
        selected: bool,
        index: int,
        subindex: Any | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        # Create dictionary of options
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        kwargs = {"region_slug": self.form.instance.region.slug}
        if value:
            kwargs["parent_id"] = value
        if self.form.instance.id:
            kwargs["page_id"] = self.form.instance.id
        option_dict["attrs"]["data-url"] = reverse(
            "get_page_order_table_ajax",
            kwargs=kwargs,
        )
        return option_dict
