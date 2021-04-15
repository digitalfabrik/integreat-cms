from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _

from backend.settings import BASE_URL


def send_activation_link(request, user_instance):
    """Sends activation link to user with inactive account

    Making use of ~django.core.mail.send_mail to prevent malicious header injections
    by raising an ~django.core.mail.BadHeaderError exception
    if a newline character is detected in subject, recipient_list, etc.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :param user_instance: The user to whom the e-mail is to be sent
    :type user_instance: ~django.contrib.auth.models.User
    """
    token = default_token_generator.make_token(user_instance)
    subject = "Activate your account"
    message = render_to_string(
        "authentication/activation_email.html",
        {
            "user": user_instance,
            "base_url": BASE_URL,
            "uid": urlsafe_base64_encode(force_bytes(user_instance.pk)),
            "token": token,
        },
    )
    try:
        # set from_email to None to use DEFAULT_FROM_EMAIL
        send_mail(subject, message, None, [user_instance.email])
        messages.success(
            request,
            _("Activation link was successfully send to user: {username}.").format(
                username=user_instance.username
            ),
        )
    except BadHeaderError:
        messages.error(
            request, "Invalid header found! Could not send activation link per mail."
        )
