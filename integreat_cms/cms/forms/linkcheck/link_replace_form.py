from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from ...constants.linkcheck import LINK_TYPES
from ...utils.linkcheck_utils import replace_links

if TYPE_CHECKING:
    from typing import Any


class LinkReplaceForm(forms.Form):
    """
    Form for link replace
    """

    search = forms.CharField(
        label=_("Search"),
        max_length=settings.LINKCHECK_MAX_URL_LENGTH,
        help_text=_("Enter old link to be replaced"),
    )
    replace = forms.CharField(
        label=_("Replace"),
        max_length=settings.LINKCHECK_MAX_URL_LENGTH,
        help_text=_("Enter new link to replace the old link with"),
    )
    link_types = forms.MultipleChoiceField(
        label=_("Link type"),
        widget=forms.CheckboxSelectMultiple(),
        choices=LINK_TYPES,
        required=True,
    )

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize link replace form

        :param \**kwargs: The supplied keyword arguments
        """
        self.region = kwargs.pop("region")
        super().__init__(**kwargs)

    def save(self) -> None:
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to call replace_link function
        """

        replace_links(
            self.cleaned_data["search"],
            self.cleaned_data["replace"],
            region=self.region,
            commit=True,
            link_types=self.cleaned_data["link_types"],
        )
