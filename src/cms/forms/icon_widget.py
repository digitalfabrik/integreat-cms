from django import forms


class IconWidget(forms.ClearableFileInput):
    """
    A custom widget to render the icon field
    """

    #: The template to use for this widget
    template_name = "icon_widget.html"
