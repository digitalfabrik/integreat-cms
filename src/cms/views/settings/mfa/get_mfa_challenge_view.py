"""
This module contains all views related to multi-factor authentication
"""
import webauthn

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from ....decorators import modify_mfa_authenticated
from ....utils.mfa_utils import generate_challenge


@method_decorator(login_required, name="dispatch")
@method_decorator(modify_mfa_authenticated, name="dispatch")
class GetMfaChallengeView(View):
    """
    View to generate a challenge for multi-factor-authentication
    """

    def get(self, request):
        """
        Return MFA challenge

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :return: The mfa challenge as JSON
        :rtype: ~django.http.JsonResponse
        """

        challenge = generate_challenge(32)
        request.session["mfa_registration_challenge"] = challenge

        user = request.user

        make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
            challenge,
            "Integreat",
            settings.HOSTNAME,
            user.id,
            user.username,
            user.first_name + " " + user.last_name,
            "",
        )
        return JsonResponse(make_credential_options.registration_dict)
