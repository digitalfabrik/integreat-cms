from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import views as auth_views
from django.shortcuts import render

from ....utils.mfa_utils import get_mfa_user

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class WebAuthnLoginView(auth_views.LoginView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/login_webauthn.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Renders the login form for TOTP authentication

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied kwargs
        :return: Rendered login form
        """
        has_totp = False
        passwordless_route = False
        if user := get_mfa_user(request):
            has_totp = user.totp_key is not None
            passwordless_route = (
                user.passwordless_authentication_enabled
                and "passwordless" in request.META["HTTP_REFERER"]
            )
        return render(
            request,
            self.template_name,
            {"has_totp": has_totp, "passwordless_route": passwordless_route},
        )
