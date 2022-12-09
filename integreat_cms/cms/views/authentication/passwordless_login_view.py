import logging

from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from integreat_cms.cms.forms.users.passwordless_authentication_form import (
    PasswordlessAuthenticationForm,
)


logger = logging.getLogger(__name__)
authlog = logging.getLogger("auth")


class PasswordlessLoginView(auth_views.LoginView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: A boolean that controls whether or not authenticated users accessing the login page will be redirected as if they
    #: had just successfully logged in.
    redirect_authenticated_user = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/passwordless_login.html"
    #: The form class for the passwordless login
    form_class = PasswordlessAuthenticationForm

    def form_valid(self, form):
        """
        This function overwrites :meth:`~django.views.generic.edit.FormMixin.form_valid` which is called if the login
        form is valid. In case the user has mfa-keys configured, the login is delegated to
        :class:`~integreat_cms.cms.views.authentication.mfa.mfa_login_view.MfaLoginView` or :class:`~integreat_cms.cms.views.authentication.totp_login_view.TOTPLoginView`. Else, the default method
        :func:`~django.contrib.auth.login` is used to log the user in. After that, the user is redirected to
        :attr:`~integreat_cms.core.settings.LOGIN_REDIRECT_URL`.

        :param form: User login form
        :type form: ~django.contrib.auth.forms.AuthenticationForm

        :return: Redirect user to mfa login view or to :attr:`~integreat_cms.core.settings.LOGIN_REDIRECT_URL`
        :rtype: ~django.http.HttpResponseRedirect
        """
        authlog.info("User %r started passwordless authentication", form.user)

        if form.user.mfa_keys.exists():
            self.request.session["mfa_user_id"] = form.user.id
            return redirect("public:login_mfa")

        if form.user.totp_key:
            self.request.session["mfa_user_id"] = form.user.id
            return redirect("public:login_totp")

        return redirect("public:login")
