from __future__ import annotations

import logging
import re

from django import forms
from django.core.validators import EmailValidator, URLValidator
from django.utils.translation import gettext_lazy as _

from ...utils.link_utils import format_phone_number

logger = logging.getLogger(__name__)


class LinkField(forms.CharField):
    """
    A field for links that might be URLs but could also be mailto: or tel: links
    """

    #: Disable the default URL validator
    default_validators: list[URLValidator | EmailValidator] = []

    def clean(self, value: str) -> str:
        """
        Validate the given value and return its "cleaned" value as an
        appropriate Python object. Raise ValidationError for any errors.

        :param value: The value that was input into the form
        :returns: The cleaned value
        """
        if "@" in value:
            email = value
            if value.startswith("mailto:"):
                email = value[7:]

            logger.debug(
                "Value %r is an email link, enforcing EmailValidator on %r",
                value,
                email,
            )
            self.validators.append(EmailValidator())
            self.error_messages["invalid"] = _("Enter a valid email address.")
            return f"mailto:{super().clean(email)}"

        if not value.startswith("tel:") and re.fullmatch(r"[+\d][\d ]*", value):
            formatted_phone_number = format_phone_number(value)
            logger.debug(
                "Value %r looks like an phone link, formatting to %r",
                value,
                formatted_phone_number,
            )
            return f"tel:{formatted_phone_number}"

        logger.debug("Value %r is a normal link, enforcing URLValidator", value)
        self.validators.append(URLValidator(schemes=["http", "https"]))
        return super().clean(value)


class EditUrlForm(forms.Form):
    """
    Form for creating and modifying Link objects
    """

    url = LinkField()
