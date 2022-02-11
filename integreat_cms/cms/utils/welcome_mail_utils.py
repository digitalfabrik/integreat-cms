import logging

from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _

from .account_activation_token_generator import account_activation_token_generator

logger = logging.getLogger(__name__)


def send_welcome_mail(request, user, activation):
    """
    Sends welcome email to user with new account.

    Making use of  :class:`~django.core.mail.EmailMultiAlternatives` and
    :class:`~email.mime.image.MIMEImage` to send a multipart email with plain text and html
    version and also attach the integreat logo.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :param user: The user to whom the e-mail is to be sent
    :type user: ~django.contrib.auth.models.User

    :param activation: Activation link should be generated
    :type activation: bool
    """
    subject = _("Welcome to your Integreat account")
    debug_mail_type = _("welcome mail")
    context = {
        "user": user,
        "base_url": settings.BASE_URL,
        "region": request.region,
    }

    if activation:
        token = account_activation_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        subject = _("Activate your Integreat account")
        debug_mail_type = _("activation mail")
        context.update(
            {
                "uid": uid,
                "token": token,
            }
        )

    text_message = render_to_string(
        "users/welcome_email.txt",
        context,
    )
    html_message = render_to_string("users/welcome_email.html", context)

    email = EmailMultiAlternatives(subject, text_message, None, [user.email])
    email.mixed_subtype = "related"
    email.attach_alternative(html_message, "text/html")

    # Attach logo
    image_path = finders.find("images/integreat-logo.png")
    if image_path:
        with open(image_path, mode="rb") as f:
            image = MIMEImage(f.read())
            email.attach(image)
            image.add_header("Content-ID", "<logo>")
    else:
        logger.debug(
            "Logo not found at %s, will proceed without attaching.",
            finders.searched_locations,
        )

    try:
        email.send()
        logger.debug(
            "%r sent an welcome mail to %r. Activation link attached: %s",
            request.user,
            user,
            activation,
        )
        messages.success(
            request,
            _("{} was successfully sent to user {}.").format(
                debug_mail_type, user.full_user_name
            ),
        )
    except BadHeaderError as e:
        logger.exception(e)
        messages.error(
            request,
            _("An error occurred! Could not send {}.").format(debug_mail_type),
        )
