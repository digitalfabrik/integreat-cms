from django import forms
from django.utils.translation import gettext_lazy as _

from ...constants.linkcheck import LINK_TYPES
from ...utils.linkcheck_utils import replace_links


class LinkReplaceForm(forms.Form):
    """
    Form for link replace
    """

    search = forms.CharField(
        label=_("Search"), max_length=64, help_text=_("Enter old link to be replaced")
    )
    replace = forms.CharField(
        label=_("Replace"),
        max_length=64,
        help_text=_("Enter new link to replace the old link with"),
    )
    link_types = forms.MultipleChoiceField(
        label=_("Link type"),
        widget=forms.CheckboxSelectMultiple(),
        choices=LINK_TYPES,
        required=True,
    )

    def __init__(self, **kwargs):
        """
        Initialize link replace form

        :param \**kwargs: The supplied keyword arguments
        :type
        """
        self.region = kwargs.pop("region")
        super().__init__(**kwargs)

    def save(self):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to call replace_link function
        """

        replace_links(
            self.cleaned_data["search"],
            self.cleaned_data["replace"],
            self.region,
            commit=True,
            link_types=self.cleaned_data["link_types"],
        )
