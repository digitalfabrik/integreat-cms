from django import forms
from django.contrib.auth.models import Group as Role


class RoleForm(forms.ModelForm):
    """
    Form for creating and modifying user role objects
    """

    class Meta:
        model = Role
        fields = ["name", "permissions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Derive size from view height (fill complete available space with select field)
        self.fields["permissions"].widget.attrs["size"] = "20"
