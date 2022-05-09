from django import forms
from django.urls import reverse


class MirroredPageFieldWidget(forms.widgets.Select):
    """
    This Widget class is used to append the url for retrieving the preview of the mirrored page to the data attributes of the options
    """

    #: The form this field is bound to
    form = None
    #: The current language slug
    language_slug = None

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
