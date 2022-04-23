import logging

from django import forms
from django.conf import settings
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.forms import PasswordResetForm

from ...utils.email_utils import send_mail

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

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.

        :param subject_template_name: The template to be used to render the subject of the email
        :type subject_template_name: str

        :param email_template_name: The template to be used to render the text email
        :type email_template_name: str

        :param context: The template context variables
        :type context: dict

        :param from_email: The email address of the sender
        :type from_email: str

        :param to_email: The email address of the recipient
        :type to_email: str

        :param html_email_template_name: The template to be used to render the HTML email
        :type html_email_template_name: str
        """
        subject = f"{capfirst(settings.BRANDING)} - {_('Reset password')}"
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
