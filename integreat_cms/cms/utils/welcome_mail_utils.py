from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from ..utils.translation_utils import gettext_many_lazy as __
from .account_activation_token_generator import account_activation_token_generator
from .email_utils import send_mail

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ..models import User

logger = logging.getLogger(__name__)


def send_welcome_mail(request: HttpRequest, user: User, activation: bool) -> None:
    """
    Sends welcome email to user with new account.

    Making use of  :class:`~django.core.mail.EmailMultiAlternatives` and
    :class:`~email.mime.image.MIMEImage` to send a multipart email with plain text and html
    version and also attach the integreat logo.

    :param request: The current http request
    :param user: The user to whom the e-mail is to be sent
    :param activation: Activation link should be generated
    """
    context = {
        "user": user,
        "BRANDING": settings.BRANDING,
        "BRANDING_TITLE": settings.BRANDING_TITLE,
    }
    subject = f"{settings.BRANDING_TITLE} - "

    if activation:
        token = account_activation_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        subject += _("Activate your account")
        debug_mail_type = _("activation mail")
        context.update(
            {
                "uid": uid,
                "token": token,
            }
        )
    else:
        subject += _("Welcome")
        debug_mail_type = _("welcome mail")

    try:
        send_mail(
            subject,
            "emails/welcome_email.txt",
            "emails/welcome_email.html",
            context,
            user.email,
        )
        logger.debug(
            "%r sent a %r to %r. Activation link attached: %s",
            request.user,
            debug_mail_type,
            user,
            activation,
        )
        messages.success(
            request,
            _("{} was successfully sent to user {}.").format(
                debug_mail_type, user.full_user_name
            ),
        )
    except RuntimeError as e:
        messages.error(
            request,
            __(
                _("An error occurred! Could not send {}.").format(debug_mail_type),
                e,
            ),
        )
