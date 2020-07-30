"""
Handling of login, logout and password reset functionality.
"""
import json
import datetime
import webauthn

from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as auth_views
from django.contrib.auth import login as auth_login
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from backend import settings

from ...utils.mfa_utils import generate_challenge


class MfaEnableAuthentication(auth_views.LoginView):
    def form_valid(self, form):
        """Security check complete. Log the user in."""

        user = form.get_user()
        if user.mfa_keys.count() > 0:
            self.request.session["mfa_user_id"] = user.id
            return redirect("login_mfa")
        auth_login(self.request, form.get_user())
        return redirect(self.get_success_url())


def login(request):
    """View to provide login functionality

    :param request: Object representing the user call
    :return: HttpResponseRedirect: View function to render the Login page
    """
    return MfaEnableAuthentication.as_view(template_name="authentication/login.html")(
        request
    )


def mfa(request):
    """View to check 2FA authentication if applicable

    :param request: Object representing the user call
    :return: HttpResponseRedirect: View function to render the MFA page
    """
    return auth_views.LoginView.as_view(template_name="authentication/login_mfa.html")(
        request
    )


def makeWebauthnUsers(user):
    webauthn_users = []

    for key in user.mfa_keys.all():
        webauthn_users.append(
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
        )

    return webauthn_users


def mfaAssert(request):
    if "mfa_user_id" not in request.session:
        return JsonResponse({"success": False, "error": _("You need to log in first")})

    if request.user.is_authenticated:
        return JsonResponse({"success": False, "error": _("You are already logged in")})
    user = get_user_model().objects.get(id=request.session["mfa_user_id"])

    challenge = generate_challenge(32)

    request.session["challenge"] = challenge
    webauthn_users = makeWebauthnUsers(user)

    webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
        webauthn_users, challenge
    )

    return JsonResponse(webauthn_assertion_options.assertion_dict)


def mfaVerify(request):
    if "mfa_user_id" not in request.session:
        return JsonResponse({"success": False, "error": _("You need to log in first")})

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
    # webauthn does not export AuthenticationRejectedException which directly extends Exception
    # as AuthenticationRejectedException is the only exception that can be raused by verify()
    # it should be okay to just except Exception
    # pylint: disable=broad-except
    except Exception as exception:
        return JsonResponse({"success": False, "error": str(exception)})

    # Update counter.
    key.sign_count = sign_count
    key.last_usage = datetime.datetime.now()
    key.save()

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return JsonResponse({"success": True})


def logout(request):
    """View to provide logout functionality

    :param request: Object representing the user call
    :return: HttpResponseRedirect: Redirect to the login page after logout
    """

    django_logout(request)
    messages.info(request, _("You have been successfully logged off."))
    return HttpResponseRedirect(reverse("login"))


def password_reset_done(request):
    """View linked to the Password reset functionality

    :param request: Object representing the user call
    :return: HttpResponseRedirect: Redirect after password reset
    """

    messages.info(
        request,
        (
            _(
                "A message with instructions for resetting your password "
                "has been sent to the e-mail address provided."
            )
        ),
    )
    return HttpResponseRedirect(reverse("password_reset"))


def password_reset_confirm(request):
    """View linked to the Password reset functionality

    :param request: Object representing the user call
    :return: PasswordChangeDoneView: Linked to Template to build view for user
    """

    template = "authentication/password_reset_confirm.html"
    return auth_views.PasswordChangeDoneView(template_name=template)


def password_reset_complete(request):
    """View linked to the Password reset functionality

    :param request: Object representing the user call
    :return: HttpResponseRedirect: Redirect to login page after password is reseted
    """

    messages.success(
        request,
        (
            _("Your password has been successfully changed.")
            / _("You can now log in with your new password.")
        ),
    )
    return HttpResponseRedirect(reverse("login"))
