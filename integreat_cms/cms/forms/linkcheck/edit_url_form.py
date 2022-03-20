from django import forms


class EditUrlForm(forms.Form):
    """
    Form for creating and modifying Link objects
    """

    url = forms.URLField()
