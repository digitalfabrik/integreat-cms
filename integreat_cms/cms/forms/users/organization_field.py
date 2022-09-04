from django.forms import ModelChoiceField
from django.forms.widgets import Select


class OrganizationFieldWidget(Select):
    """
    Select widget which puts the organization's region id as data attribute on <options>
    """

    # pylint: disable=too-many-arguments
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """
        This function creates an option which can be selected in the organization field

        :param name: The name of the option
        :type name: str

        :param value: the value of the option (the page id)
        :type value: int

        :param label: The label (and optionally the region id) of the option
        :type label: str or dict

        :param selected: Whether or not the option is selected
        :type selected: bool

        :param index: The index of the option
        :type index: int

        :param subindex: The subindex of the option
        :type subindex: int

        :param attrs: The attributes of the option
        :type attrs: dict

        :return: The option dict
        :rtype: dict
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

    def label_from_instance(self, obj):
        """
        Normally, this function convert objects into strings and
        generate the labels for the choices presented by this object.

        In this case, we abuse the function also to pass the organization's region id to the
        :func:`~integreat_cms.cms.forms.users.organization_field.OrganizationFieldWidget.create_option`
        function to enable it to use it as data attribute.

        :param obj: The name of the option
        :type obj: str

        :return: A dict of the real label and the organization's region id
        :rtype: dict
        """
        return {
            "label": super().label_from_instance(obj),  # the real label
            "data-region-id": obj.region_id,  # the new data attribute
        }
