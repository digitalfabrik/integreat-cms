from django import forms
from django.urls import reverse


class ParentFieldWidget(forms.widgets.Select):
    """
    This Widget class is used to append the url for retrieving the page order tables to the data attributes of the options
    """

    #: The form this field is bound to
    form = None

    # pylint: disable=too-many-arguments
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """
        This function creates an option which can be selected in the parent field

        :param name: The name of the option
        :type name: str

        :param value: the value of the option (the page id)
        :type value: int

        :param label: The label of the option
        :type label: str

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
