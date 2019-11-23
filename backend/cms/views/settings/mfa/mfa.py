import time
import random
import string
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
from cms.models import UserMfa
from backend import settings

from ....decorators import modify_mfa_authenticated


def generate_challenge(challenge_len):
    return ''.join([
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for i in range(challenge_len)
    ])


class AddMfaKeyForm(forms.Form):
    nickname = forms.CharField(max_length=255, required=True)


@method_decorator(login_required, name='dispatch')
@method_decorator(modify_mfa_authenticated, name='dispatch')
class AddMfaKeyView(FormView):
    template_name = 'settings/mfa/add_key.html'
    form_class = AddMfaKeyForm


class AuthenticationForm(forms.Form):
    attrs = {
        "type": "password",
        "required": True
    }
    password = forms.CharField(widget=forms.TextInput(attrs=attrs))

@method_decorator(login_required, name='dispatch')
class AuthenticateModifyMfaView(FormView):
    template_name = 'settings/mfa/authenticate.html'
    form_class = AuthenticationForm
    success_url = '/user_settings/add_new_mfa_key/'

    def form_valid(self, form):
        if check_password(form.cleaned_data['password'], self.request.user.password):
            self.request.session['modify_mfa_authentication_time'] = time.time()
            if 'mfa_redirect_url' in self.request.session:
                return redirect(self.request.session['mfa_redirect_url'])
            return super().form_valid(form)
        form.add_error('password', _('The provided password is not correct'))
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(modify_mfa_authenticated, name='dispatch')
class GetChallengeView(View):
    def get(self, request):
        challenge = generate_challenge(32)
        request.session['mfa_registration_challenge'] = challenge

        user = request.user

        make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
            challenge,
            'Integreat',
            settings.HOSTNAME,
            user.id,
            user.username,
            user.first_name + " " + user.last_name,
            '')
        return JsonResponse(make_credential_options.registration_dict)

@method_decorator(login_required, name='dispatch')
@method_decorator(modify_mfa_authenticated, name='dispatch')
class DeleteMfaKey(TemplateView):
    template_name = 'settings/mfa/delete.html'

    def get(self, request, *args, **kwargs):
        key = request.user.mfa_keys.get(id=kwargs['key_id'])
        return render(request,
                      self.template_name,
                      {'key': key,
                       'last_key': request.user.mfa_keys.count() == 1})

    def post(self, request, **kwargs):
        key = request.user.mfa_keys.get(id=kwargs['key_id'])
        key.delete()
        return redirect('user_settings')


def register_mfa_key(request):
    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        settings.HOSTNAME,
        settings.BASE_URL,
        json.loads(request.body)['assertion'],
        request.session['mfa_registration_challenge'])

    webauthn_credential = webauthn_registration_response.verify()

    existing_key = request.user.mfa_keys.filter(name=json.loads(request.body)['nickname'])
    if len(existing_key) > 0:
        return JsonResponse({'success': False, 'error': _('This nickname has already been used')})

    existing_key = request.user.mfa_keys.filter(key_id=webauthn_credential.credential_id)
    if len(existing_key) > 0:
        return JsonResponse({'success': False, 'error': _('You already registered this key')})

    new_key = UserMfa(
        user=request.user,
        name=json.loads(request.body)['nickname'],
        key_id=webauthn_credential.credential_id,
        public_key=webauthn_credential.public_key,
        sign_count=webauthn_credential.sign_count
    )
    new_key.save()
    return JsonResponse({'success': True})
