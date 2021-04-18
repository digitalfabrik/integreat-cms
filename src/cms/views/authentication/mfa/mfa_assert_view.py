import logging
import webauthn

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.translation import ugettext as _
from django.views.generic import View

from ....utils.mfa_utils import generate_challenge

logger = logging.getLogger(__name__)


class MfaAssertView(View):
    """
    Generate challenge for multi factor authentication.
    If the user did not provide the first factor (password) or already authenticated with multiple factors, an error is
    returned.
    This AJAX view is called asynchronously by JavaScript.
    """

    def get(self, request):
        """

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :return: The mfa challenge as JSON
        :rtype: ~django.http.JsonResponse
        """
        if "mfa_user_id" not in request.session:
            return JsonResponse(
                {"success": False, "error": _("You need to log in first")}
            )

        if request.user.is_authenticated:
            return JsonResponse(
                {"success": False, "error": _("You are already logged in.")}
            )
        user = get_user_model().objects.get(id=request.session["mfa_user_id"])

        challenge = generate_challenge(32)

        request.session["challenge"] = challenge

        webauthn_users = [
            webauthn.WebAuthnUser(
                user.id,
                user.username,
                "%s %s" % (user.first_name, user.last_name),
                "",
                str(key.key_id, "utf-8"),
                key.public_key,
                key.sign_count,
                settings.HOSTNAME,
            )
            for key in user.mfa_keys.all()
        ]

        webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
            webauthn_users, challenge
        )

        return JsonResponse(webauthn_assertion_options.assertion_dict)
