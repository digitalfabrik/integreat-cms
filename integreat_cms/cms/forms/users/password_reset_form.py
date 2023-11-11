from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _

from ...utils.email_utils import send_mail

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class CustomPasswordResetForm(PasswordResetForm):
    """
    A custom form to attach the logo to the password reset email
    """

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    # pylint: disable=signature-differs
    def send_mail(
        self,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, Any],
        from_email: Any | None,
        to_email: str,
        html_email_template_name: str,
    ) -> None:
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.

        :param subject_template_name: The template to be used to render the subject of the email
        :param email_template_name: The template to be used to render the text email
        :param context: The template context variables
        :param from_email: The email address of the sender
        :param to_email: The email address of the recipient
        :param html_email_template_name: The template to be used to render the HTML email
        """
        subject = f"{settings.BRANDING_TITLE} - {_('Reset password')}"
        send_mail(
            subject,
            email_template_name,
            html_email_template_name,
            context,
            to_email,
        )
        logger.info(
            "A password reset link was sent to email %r.",
            to_email,
        )
