from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from webauthn import base64url_to_bytes, verify_authentication_response
from webauthn.helpers import parse_authentication_credential_json
from webauthn.helpers.exceptions import InvalidAuthenticationResponse

if TYPE_CHECKING:
    from django.http import HttpRequest

from ....utils.mfa_utils import get_mfa_user

logger = logging.getLogger(__name__)


class WebAuthnVerifyView(View):
    """
    Verify the response to the challenge generated in :class:`~integreat_cms.cms.views.authentication.webauthn.webauthn_assert_view.WebAuthnAssertView`.
    After a successful verification, the user is logged in.
    """

    def post(self, request: HttpRequest) -> JsonResponse:
        """

        :param request: The current request
        :return: The mfa challenge as JSON
        """
        if not (user := get_mfa_user(request)):
            return JsonResponse(
                {"success": False, "error": _("You need to log in first")}, status=403
            )

        challenge = request.session["challenge"]
        assertion_response = json.loads(request.body)
        credential_id = assertion_response["id"]

        key = user.fido_keys.get(key_id=base64url_to_bytes(credential_id))

        try:
            authentication_verification = verify_authentication_response(
                credential=parse_authentication_credential_json(
                    json.loads(request.body)
                ),
                expected_challenge=base64url_to_bytes(challenge),
                expected_rp_id=settings.HOSTNAME,
                expected_origin=settings.BASE_URL,
                credential_public_key=key.public_key,
                credential_current_sign_count=key.sign_count,
            )
        except InvalidAuthenticationResponse as e:
            logger.exception(e)
            return JsonResponse(
                {"success": False, "error": "Authentication rejected"}, status=403
            )

        # Update counter.
        key.sign_count = authentication_verification.new_sign_count
        key.last_usage = datetime.datetime.now()
        key.save()

        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        return JsonResponse({"success": True})
