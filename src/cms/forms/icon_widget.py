from django import forms
from ..models import Document


class IconWidget(forms.HiddenInput):
    """
    A custom widget to render the icon field
    """

    #: The template to use for this widget
    template_name = "icon_widget.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            context["widget"]["document"] = Document.objects.get(id=value)

        return context
