from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pyotp
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import modify_mfa_authenticated
from ...utils.totp_utils import check_totp_code, generate_totp_qrcode

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class TOTPRegisterView(TemplateView):
    """
    View to register a TOTP authenticator.
    """

    template_name = "settings/register_totp.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Initialize the registration for the authentication application.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: A redirection to the account settings
        """
        if request.user.totp_key:
            messages.error(
                request,
                _(
                    "You have already registered a TOTP key. Please disconnect your app before adding a new one."
                ),
            )
            kwargs = {"region_slug": request.region.slug} if request.region else {}
            return redirect("user_settings", **kwargs)
        # Generate random key for validation
        key = pyotp.random_base32()
        # Generate QR-Code for registration in authenticator
        qrcode = generate_totp_qrcode(key, request.user)
        # Save key to session to keep the same key after redirect on error
        request.session["new_totp_key"] = key
        return render(request, self.template_name, context={"qr": qrcode})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        View to validate the connection between the authenticator app and the user account.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: A redirection to the account settings
        """
        totp_code = request.POST.get("totp")
        key = request.session["new_totp_key"]

        if check_totp_code(totp_code, key):
            user = request.user
            user.totp_key = key
            user.save()
            logger.info(
                "Account %r added TOTP as a authentication method.", request.user
            )
            messages.success(
                request, _("The TOTP Authenticator has been added successfully.")
            )
            # Clear session variable
            del request.session["new_totp_key"]
            kwargs = {"region_slug": request.region.slug} if request.region else {}
            return redirect("user_settings", **kwargs)

        logger.error("Account %r failed to activate TOTP.", request.user)
        messages.error(
            request,
            _("Something went wrong. Please check the generated code and try again."),
        )
        return render(
            request,
            self.template_name,
            context={"qr": generate_totp_qrcode(key, request.user)},
        )
