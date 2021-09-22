import logging
import json

import webauthn

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView

from ....models import UserMfaKey
from ....decorators import modify_mfa_authenticated

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(modify_mfa_authenticated, name="dispatch")
class RegisterUserMfaKeyView(CreateView):
    """
    View to render a form for creating :class:`~cms.models.users.user_mfa_key.UserMfaKey` objects
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/add_key.html"
    #: The model of this :class:`~django.views.generic.edit.CreateView`
    model = UserMfaKey
    #: The fields of the model which should be handled by this create view
    fields = [
        "name",
    ]

    def post(self, request, *args, **kwargs):
        """
        Verify a registration challenge and register a 2-FA key.
        Called asynchroniously by JavaScript.

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The JSON response
        :rtype: ~django.http.JsonResponse
        """
        json_data = json.loads(request.body)

        webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
            settings.HOSTNAME,
            settings.BASE_URL,
            json_data["assertion"],
            request.session["mfa_registration_challenge"],
        )

        webauthn_credential = webauthn_registration_response.verify()

        existing_key = request.user.mfa_keys.filter(name=json_data["name"])
        if existing_key.exists():
            return JsonResponse(
                {"success": False, "error": _("This key name has already been used")}
            )

        existing_key = request.user.mfa_keys.filter(
            key_id=webauthn_credential.credential_id
        )
        if existing_key.exists():
            return JsonResponse(
                {"success": False, "error": _("You already registered this key")}
            )

        new_key = UserMfaKey(
            user=request.user,
            name=json_data["name"],
            key_id=webauthn_credential.credential_id,
            public_key=webauthn_credential.public_key,
            sign_count=webauthn_credential.sign_count,
        )
        new_key.save()
        messages.success(
            request,
            _(
                'The 2-factor authentication key "{}" was successfully registered.'
            ).format(new_key.name),
        )
        # Determine success url
        if request.user.is_superuser or request.user.is_staff:
            # If user is superuser, return to user settings in network area
            success_url = reverse("user_settings")
        else:
            # If user is region-user, return to user settings in first region
            success_url = reverse(
                "user_settings",
                kwargs={"region_slug": request.user.regions.first().slug},
            )
        return JsonResponse({"success": True, "successUrl": success_url})
