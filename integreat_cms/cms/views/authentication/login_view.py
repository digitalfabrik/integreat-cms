from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

if TYPE_CHECKING:
    from django.contrib.auth.forms import AuthenticationForm
    from django.http.response import HttpResponseRedirect

logger = logging.getLogger(__name__)


class LoginView(auth_views.LoginView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: A boolean that controls whether or not authenticated users accessing the login page will be redirected as if they
    #: had just successfully logged in.
    redirect_authenticated_user = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/login.html"

    def form_valid(self, form: AuthenticationForm) -> HttpResponseRedirect:
        """
        This function overwrites :meth:`~django.views.generic.edit.FormMixin.form_valid` which is called if the login
        form is valid. In case the user has mfa-keys configured, the login is delegated to
        :class:`~integreat_cms.cms.views.authentication.webauthn.webauthn_login_view.WebAuthnLoginView`. Else, the default method
        :func:`~django.contrib.auth.login` is used to log the user in. After that, the user is redirected to
        :attr:`~integreat_cms.core.settings.LOGIN_REDIRECT_URL`.

        :param form: User login form
        :return: Redirect user to mfa login view or to :attr:`~integreat_cms.core.settings.LOGIN_REDIRECT_URL`
        """

        user = form.get_user()

        if not user.passwordless_authentication_enabled:
            if user.fido_keys.exists():
                self.request.session["mfa_user_id"] = user.id
                return redirect("public:login_webauthn")

            if user.totp_key:
                self.request.session["mfa_user_id"] = user.id
                return redirect("public:login_totp")

        auth_login(self.request, form.get_user())
        return redirect(self.get_success_url())
