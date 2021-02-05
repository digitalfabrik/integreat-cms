"""
This module contains helpers for the account activation process
(also see :class:`~cms.views.authentication.account_activation_view.AccountActivationView`).
"""
import logging

from django.contrib import messages
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _

from backend.settings import BASE_URL
from ..models import Region

logger = logging.getLogger(__name__)


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    This token generator is identical to the default password reset token generator of :mod:`django.contrib.auth` with
    the exception of the used HMAC salt.
    This means password reset tokens are no longer accepted for the account activation and vice versa.
    """

    #: The key salt which is passed to the HMAC function
    key_salt = "cms.utils.account_activation_utils.AccountActivationTokenGenerator"


#: The token generator for the account activation process
#: (an instance of :class:`~cms.utils.account_activation_utils.AccountActivationTokenGenerator`)
account_activation_token_generator = AccountActivationTokenGenerator()


def send_activation_link(request, user):
    """
    Sends activation link to user with inactive account

    Making use of :func:`~django.core.mail.send_mail` to prevent malicious header injections by raising an
    ``BadHeaderError`` exception if a newline character is detected in ``subject``,
    ``recipient_list``, etc. (see :doc:`django:topics/email`).

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :param user: The user to whom the e-mail is to be sent
    :type user: ~django.contrib.auth.models.User
    """
    region = Region.get_current_region(request)
    token = account_activation_token_generator.make_token(user)
    subject = _("Activate your Integreat account")
    message = render_to_string(
        "authentication/activation_email.html",
        {
            "user": user,
            "base_url": BASE_URL,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token,
            "region": region,
        },
    )
    try:
        # set from_email to None to use DEFAULT_FROM_EMAIL
        send_mail(subject, message, None, [user.email])
        logger.debug(
            "%r sent an account activation mail to %r",
            request.user.profile,
            user.profile,
        )
        messages.success(
            request,
            _("Activation link was successfully sent to user {}.").format(
                user.profile.full_user_name
            ),
        )
    except BadHeaderError as e:
        logger.exception(e)
        messages.error(
            request, _("An error occurred! Could not send activation link per mail.")
        )
