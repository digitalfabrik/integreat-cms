import logging
import json
from webauthn import verify_registration_response, base64url_to_bytes
from webauthn.helpers.structs import RegistrationCredential

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView

from ....models import UserMfaKey
from ....decorators import modify_mfa_authenticated

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class RegisterUserMfaKeyView(CreateView):
    """
    View to render a form for creating :class:`~integreat_cms.cms.models.users.user_mfa_key.UserMfaKey` objects
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
        r"""
        Verify a registration challenge and register a 2-FA key.
        Called asynchronously by JavaScript.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The JSON response
        :rtype: ~django.http.JsonResponse
        """
        json_data = json.loads(request.body)

        webauthn_registration_response = verify_registration_response(
            credential=RegistrationCredential.parse_raw(request.body),
            expected_rp_id=settings.HOSTNAME,
            expected_origin=settings.BASE_URL,
            expected_challenge=base64url_to_bytes(
                request.session["mfa_registration_challenge"]
            ),
        )

        existing_key = request.user.mfa_keys.filter(name=json_data["name"])
        if existing_key.exists():
            return JsonResponse(
                {"success": False, "error": _("This key name has already been used")}
            )

        existing_key = request.user.mfa_keys.filter(
            key_id=webauthn_registration_response.credential_id
        )
        if existing_key.exists():
            return JsonResponse(
                {"success": False, "error": _("You already registered this key")}
            )

        new_key = UserMfaKey(
            user=request.user,
            name=json_data["name"],
            key_id=webauthn_registration_response.credential_id,
            public_key=webauthn_registration_response.credential_public_key,
            sign_count=webauthn_registration_response.sign_count,
        )
        new_key.save()
        messages.success(
            request,
            _(
                'The 2-factor authentication key "{}" was successfully registered.'
            ).format(new_key.name),
        )
        # Determine success url based on current region
        kwargs = {"region_slug": request.region.slug} if request.region else {}
        success_url = reverse("user_settings", kwargs=kwargs)
        return JsonResponse({"success": True, "successUrl": success_url})
