"""
This module contains all views related to multi-factor authentication
"""
import time
import json

import webauthn
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django import forms
from django.views.generic.edit import FormView
from django.contrib.auth.hashers import check_password
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect

from backend import settings

from ....models import UserMfa
from ....decorators import modify_mfa_authenticated
from ....utils.mfa_utils import generate_challenge


class AddMfaKeyForm(forms.Form):
    """
    Form to add an multi-factor-authentication key
    """

    nickname = forms.CharField(max_length=255, required=True)


@method_decorator(login_required, name="dispatch")
@method_decorator(modify_mfa_authenticated, name="dispatch")
class AddMfaKeyView(FormView):
    """
    View to render and submit the :class:`~cms.views.settings.mfa.mfa.AddMfaKeyForm`
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/add_key.html"
    #: The form class to instantiate for this form view (see :class:`~django.views.generic.edit.FormMixin`)
    form_class = AddMfaKeyForm


class AuthenticationForm(forms.Form):
    """
    Form to authenticate a user
    """

    attrs = {"type": "password", "required": True}
    password = forms.CharField(widget=forms.TextInput(attrs=attrs))


@method_decorator(login_required, name="dispatch")
class AuthenticateModifyMfaView(FormView):
    """
    View to authenticate a user before changing the mfa settings
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/authenticate.html"
    #: The form class for this form view (see :class:`~django.views.generic.edit.FormMixin`)
    form_class = AuthenticationForm
    #: The URL to redirect to when the form is successfully processed (see :class:`~django.views.generic.edit.FormMixin`)
    success_url = "/user_settings/add_new_mfa_key/"

    def form_valid(self, form):
        """
        This function overwrites :meth:`~django.views.generic.edit.FormMixin.form_valid` which is called if the
        :class:`~cms.views.settings.mfa.mfa.AuthenticationForm` is valid. In case the user provided correct credentials,
        the current time is saved in a session variable so a timeout of the authentication can be implemented.

        :param form: Authentication form
        :type form: ~cms.views.settings.mfa.mfa.AuthenticationForm

        :return: Redirect user to mfa login view or to :attr:`~backend.settings.LOGIN_REDIRECT_URL`
        :rtype: ~django.http.HttpResponseRedirect
        """
        if check_password(form.cleaned_data["password"], self.request.user.password):
            self.request.session["modify_mfa_authentication_time"] = time.time()
            if "mfa_redirect_url" in self.request.session:
                return redirect(self.request.session["mfa_redirect_url"])
            return super().form_valid(form)
        form.add_error("password", _("The provided password is not correct"))
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
@method_decorator(modify_mfa_authenticated, name="dispatch")
class GetChallengeView(View):
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


@method_decorator(login_required, name="dispatch")
@method_decorator(modify_mfa_authenticated, name="dispatch")
class DeleteMfaKey(TemplateView):
    """
    View to delete a multi-factor-authentication key
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/delete.html"

    def get(self, request, *args, **kwargs):
        """
        Render mfa-deletion view

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        key = request.user.mfa_keys.get(id=kwargs["key_id"])
        return render(
            request,
            self.template_name,
            {"key": key, "last_key": request.user.mfa_keys.count() == 1},
        )

    def post(self, request, **kwargs):
        """
        Delete a multi-factor-authentication key

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: A redirection to the user settings
        :rtype: ~django.http.HttpResponseRedirect
        """

        key = request.user.mfa_keys.get(id=kwargs["key_id"])
        key.delete()
        return redirect("user_settings")


def register_mfa_key(request):
    """
    View to register a multi-factor-authentication key

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :return: The success status as JSON
    :rtype: ~django.http.JsonResponse
    """

    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        settings.HOSTNAME,
        settings.BASE_URL,
        json.loads(request.body)["assertion"],
        request.session["mfa_registration_challenge"],
    )

    webauthn_credential = webauthn_registration_response.verify()

    existing_key = request.user.mfa_keys.filter(
        name=json.loads(request.body)["nickname"]
    )
    if existing_key.exists():
        return JsonResponse(
            {"success": False, "error": _("This nickname has already been used")}
        )

    existing_key = request.user.mfa_keys.filter(
        key_id=webauthn_credential.credential_id
    )
    if existing_key.exists():
        return JsonResponse(
            {"success": False, "error": _("You already registered this key")}
        )

    new_key = UserMfa(
        user=request.user,
        name=json.loads(request.body)["nickname"],
        key_id=webauthn_credential.credential_id,
        public_key=webauthn_credential.public_key,
        sign_count=webauthn_credential.sign_count,
    )
    new_key.save()
    return JsonResponse({"success": True})
