import json
import datetime
import logging
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

logger = logging.getLogger(__name__)


class MfaEnableAuthentication(auth_views.LoginView):
    """
    View to extend the default login behaviour from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    def form_valid(self, form):
        """
        This function overwrites :meth:`~django.views.generic.edit.FormMixin.form_valid` which is called if the login
        form is valid. In case the user has mfa-keys configured, the login is delegated to
        :func:`~cms.views.authentication.authentication_actions.mfa`. Else, the default method
        :func:`~django.contrib.auth.login` is used to log the user in. After that, the user is redirected to
        :attr:`~backend.settings.LOGIN_REDIRECT_URL`.

        :param form: User login form
        :type form: ~django.contrib.auth.forms.AuthenticationForm

        :return: Redirect user to mfa login view or to :attr:`~backend.settings.LOGIN_REDIRECT_URL`
        :rtype: ~django.http.HttpResponseRedirect
        """

        user = form.get_user()
        if user.mfa_keys.count() > 0:
            self.request.session["mfa_user_id"] = user.id
            return redirect("login_mfa")
        auth_login(self.request, form.get_user())
        return redirect(self.get_success_url())


def login(request):
    """
    View for the login. Aliased to :class:`~cms.views.authentication.authentication_actions.MfaEnableAuthentication`

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: The login form
    :rtype: ~django.template.response.TemplateResponse
    """

    return MfaEnableAuthentication.as_view(template_name="authentication/login.html")(
        request
    )


def mfa(request):
    """
    View to check 2FA authentication. Aliased to :class:`~django.contrib.auth.views.LoginView` with a custom template.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: The second factor form
    :rtype: ~django.template.response.TemplateResponse
    """

    return auth_views.LoginView.as_view(template_name="authentication/login_mfa.html")(
        request
    )


def makeWebauthnUsers(user):
    """
    Create WebAuthnUser objects for each mfa key of the user (see `webauthn <https://pypi.org/project/webauthn/>`_ for
    more information)

    :param user: The user object of this webauthn assertion
    :type user: ~django.contrib.auth.models.User

    :return: The list ob webauthn user objects
    :rtype: list [ ~webauthn.WebAuthnUser ]
    """

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
    """
    Generate challenge for multi factor authentication.
    If the user did not provide the first factor (password) or already authenticated with multiple factors, an error is
    returned.
    This AJAX view is called asynchronously by JavaScript.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: Error message or challenge for multi factor authentication
    :rtype: ~django.http.JsonResponse
    """

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
    """
    Verify the response to the challenge generated in :func:`~cms.views.authentication.authentication_actions.mfaAssert`.
    After a successful verification, the user is logged in.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: Whether or not the verification was successful
    :rtype: ~django.http.JsonResponse
    """

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
    except webauthn.webauthn.AuthenticationRejectedException as e:
        logger.exception(e)
        return JsonResponse({"success": False, "error": str(e)})

    # Update counter.
    key.sign_count = sign_count
    key.last_usage = datetime.datetime.now()
    key.save()

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return JsonResponse({"success": True})


def logout(request):
    """
    View to log off a user

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: HttpResponseRedirect: Redirect to the login page after logout
    :rtype: ~django.http.HttpResponseRedirect
    """

    django_logout(request)
    messages.info(request, _("You have been successfully logged off."))
    return HttpResponseRedirect(reverse("login"))


def password_reset_done(request):
    """
    View to indicate that the password reset process has been initiated

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: Redirect after password reset
    :rtype: ~django.http.HttpResponseRedirect
    """

    logger.debug(
        "Password reset process for %r has been initiated", request.user.profile
    )
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
    """
    View to confirm that the password should be reset

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: PasswordChangeDoneView: Linked to Template to build view for user
    :rtype: ~django.contrib.auth.views.PasswordChangeDoneView
    """

    template = "authentication/password_reset_confirm.html"
    return auth_views.PasswordChangeDoneView(template_name=template)


def password_reset_complete(request):
    """
    View to indicate that the password was successfully reset

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :return: Redirect to login page after password is reseted
    :rtype: ~django.http.HttpResponseRedirect
    """

    logger.info("Password of %r was reset", request.user.profile)
    messages.success(
        request,
        (
            _("Your password has been successfully changed.")
            / _("You can now log in with your new password.")
        ),
    )
    return HttpResponseRedirect(reverse("login"))
