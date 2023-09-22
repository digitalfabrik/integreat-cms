import logging

from django.contrib.auth import views as auth_views
from django.shortcuts import render

from ....utils.mfa_utils import get_mfa_user

logger = logging.getLogger(__name__)


class WebAuthnLoginView(auth_views.LoginView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/login_webauthn.html"

    def get(self, request, *args, **kwargs):
        r"""
        Renders the login form for TOTP authentication

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied kwargs
        :type \**kwargs: dict

        :return: Rendered login form
        :rtype: ~django.http.HttpResponse
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
