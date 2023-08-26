import logging

from django.conf import settings
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import View
from webauthn import generate_authentication_options, options_to_json
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from integreat_cms.cms.utils.mfa_utils import get_mfa_user

logger = logging.getLogger(__name__)


class WebAuthnAssertView(View):
    """
    Generate challenge for multi factor authentication.
    If the user did not provide the first factor (password) or already authenticated with multiple factors, an error is
    returned.
    This AJAX view is called asynchronously by JavaScript.
    """

    def get(self, request):
        """

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :return: The mfa challenge as JSON
        :rtype: ~django.http.JsonResponse
        """
        if not (user := get_mfa_user(request)):
            return JsonResponse(
                {"success": False, "error": _("You need to log in first")}, status=403
            )

        if request.user.is_authenticated:
            return JsonResponse(
                {"success": False, "error": _("You are already logged in.")}
            )

        webauthn_challenge = generate_authentication_options(
            rp_id=settings.HOSTNAME,
            allow_credentials=[
                PublicKeyCredentialDescriptor(id=key.key_id)
                for key in user.fido_keys.all()
            ],
        )

        request.session["challenge"] = bytes_to_base64url(webauthn_challenge.challenge)

        # pylint: disable=http-response-with-content-type-json
        return HttpResponse(
            options_to_json(webauthn_challenge), content_type="application/json"
        )
