from __future__ import annotations

import logging

from django.utils.translation import gettext_lazy as _

from ...models import UserApiToken
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserApiTokenForm(CustomModelForm):
    """
    Form for creating a personal API token
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class,
        see the :class:`django.forms.ModelForm` for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = UserApiToken
        #: The fields of the model which should be handled by this form
        fields = ["name"]

    def __init__(self, *args: object, **kwargs: object) -> None:
        r"""
        Store the user the token is created for so the name can be validated against their
        existing tokens.

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_name(self) -> str:
        """
        Ensure that the token name is not already used by another token of the same user.

        :return: The validated token name
        """
        name = self.cleaned_data.get("name")
        if (
            name
            and self.user
            and UserApiToken.objects.filter(user=self.user, name=name).exists()
        ):
            self.add_error("name", _("You already have a token with this name."))
        return name
