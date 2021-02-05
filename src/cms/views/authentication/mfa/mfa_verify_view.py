import json
import datetime
import logging
import webauthn

from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.utils.translation import ugettext as _
from django.http import JsonResponse
from django.views.generic import View

logger = logging.getLogger(__name__)


class MfaVerifyView(View):
    """
    Verify the response to the challenge generated in :class:`~cms.views.authentication.mfa.mfa_assert_view.MfaAssertView`.
    After a successful verification, the user is logged in.
    """

    def post(self, request):
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

        user = get_user_model().objects.get(id=request.session["mfa_user_id"])

        challenge = request.session["challenge"]
        assertion_response = json.loads(request.body)
        credential_id = assertion_response["id"]
        key = user.mfa_keys.get(key_id=credential_id.encode("ascii"))

        webauthn_user = webauthn.WebAuthnUser(
            user.id,
            user.username,
            "%s %s" % (user.first_name, user.last_name),
            "",
            str(key.key_id, "utf-8"),
            str(key.public_key, "utf-8"),
            key.sign_count,
            settings.HOSTNAME,
        )

        webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
            webauthn_user, assertion_response, challenge, settings.BASE_URL
        )

        try:
            sign_count = webauthn_assertion_response.verify()
        except webauthn.webauthn.AuthenticationRejectedException as e:
            logger.exception(e)
            return JsonResponse({"success": False, "error": "Authentication rejected"})

        # Update counter.
        key.sign_count = sign_count
        key.last_usage = datetime.datetime.now()
        key.save()

        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        return JsonResponse({"success": True})
