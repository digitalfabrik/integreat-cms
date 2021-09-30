from django import forms


class ObjectSearchForm(forms.Form):
    """
    Form for searching objects
    """

    query = forms.CharField(min_length=1, required=False)
