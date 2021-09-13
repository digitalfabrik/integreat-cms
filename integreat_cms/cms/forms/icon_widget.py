from django import forms
from ..models import MediaFile


class IconWidget(forms.HiddenInput):
    """
    A custom widget to render the icon field
    """

    #: The template to use for this widget
    template_name = "icon_widget.html"

    def get_context(self, name, value, attrs):
        """
        This function gets the context of icon fields

        :param name: the supplied name
        :type name: str

        :param value: the supplied values
        :type value: str

        :param attrs: the supplied attrs
        :type attrs: list

        :return: context
        :rtype: dict
        """

        context = super().get_context(name, value, attrs)
        if value:
            context["widget"]["document"] = MediaFile.objects.get(id=value)

        return context
