"""
Form for creating a group object
"""

from django import forms
from django.contrib.auth.models import Group as Role


class RoleForm(forms.ModelForm):
    """
    DjangoForm Class, that can be rendered to create deliverable HTML

    Args:
        forms : Defines the form as an Model form related to a database object
    """

    class Meta:
        model = Role
        fields = ['name', 'permissions']

    def __init__(self, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        # TODO: Derive size from view height (fill complete available space with select field)
        self.fields['permissions'].widget.attrs['size'] = '20'
