from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms

from ..models import MediaFile

if TYPE_CHECKING:
    from typing import Any


class IconWidget(forms.HiddenInput):
    """
    A custom widget to render the icon field
    """

    #: The template to use for this widget
    template_name = "icon_widget.html"

    def get_context(
        self, name: str, value: Any | None, attrs: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        This function gets the context of icon fields

        :param name: the supplied name
        :param value: the supplied values
        :param attrs: the supplied attrs
        :return: context
        """

        context = super().get_context(name, value, attrs)
        if value:
            context["widget"]["document"] = MediaFile.objects.get(id=value)

        return context
