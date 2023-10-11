from __future__ import annotations

from typing import TYPE_CHECKING

from django.forms import ModelChoiceField
from django.forms.widgets import Select

if TYPE_CHECKING:
    from typing import Any

    from django.forms.models import ModelChoiceIteratorValue

    from ...models import Organization


class OrganizationFieldWidget(Select):
    """
    Select widget which puts the organization's region id as data attribute on <options>
    """

    # pylint: disable=too-many-arguments
    def create_option(
        self,
        name: str,
        value: ModelChoiceIteratorValue | str,
        label: dict[str, Any] | str,
        selected: bool,
        index: int,
        subindex: Any | None = None,
        attrs: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        This function creates an option which can be selected in the organization field

        :param name: The name of the option
        :param value: the value of the option (the page id)
        :param label: The label (and optionally the region id) of the option
        :param selected: Whether or not the option is selected
        :param index: The index of the option
        :param subindex: The subindex of the option
        :param attrs: The attributes of the option
        :return: The option dict
        """
        # If our "hacky" dict is given as label, get the real string label
        if isinstance(label, dict):
            region_id = label["data-region-id"]
            label = label["label"]
        else:
            # For the initial label "---------" we don't get a region id
            region_id = None
        # Create dictionary of options
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if region_id:
            # Add organization's region id as data attribute
            option_dict["attrs"]["data-region-id"] = region_id
        return option_dict


class OrganizationField(ModelChoiceField):
    """
    ModelChoiceField which puts the organization's region id as data attribute on <options>
    """

    #: The widget to use when rendering this type of Field.
    widget = OrganizationFieldWidget

    def label_from_instance(self, obj: Organization) -> dict[str, Any]:
        """
        Normally, this function convert objects into strings and
        generate the labels for the choices presented by this object.

        In this case, we abuse the function also to pass the organization's region id to the
        :func:`~integreat_cms.cms.forms.users.organization_field.OrganizationFieldWidget.create_option`
        function to enable it to use it as data attribute.

        :param obj: The name of the option
        :return: A dict of the real label and the organization's region id
        """
        return {
            "label": super().label_from_instance(obj),  # the real label
            "data-region-id": obj.region_id,  # the new data attribute
        }
