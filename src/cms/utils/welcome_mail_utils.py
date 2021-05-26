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


def send_welcome_mail(request, user):
    subject = _("Welcome to your Integreat account")
    message = render_to_string(
        "users/welcome_email.html",
        {"user": user, "base_url": BASE_URL},
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
