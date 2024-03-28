"""
This module contains all views related to multi-factor authentication
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from webauthn import generate_registration_options, options_to_json
from webauthn.helpers import bytes_to_base64url

from ....decorators import modify_mfa_authenticated

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class GetMfaChallengeView(View):
    """
    View to generate a challenge for multi-factor-authentication
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Return MFA challenge

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The mfa challenge as JSON
        """

        user = request.user

        make_credential_options = generate_registration_options(
            rp_name="Integreat",
            rp_id=settings.HOSTNAME,
            user_id=user.webauthn_id,
            user_name=user.username,
            user_display_name=user.first_name + " " + user.last_name,
        )
        request.session["mfa_registration_challenge"] = bytes_to_base64url(
            make_credential_options.challenge
        )
        # pylint: disable=http-response-with-content-type-json
        return HttpResponse(
            options_to_json(make_credential_options), content_type="application/json"
        )
