from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...utils.totp_utils import check_totp_code
from ...utils.translation_utils import gettext_many_lazy as __

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from ..models import User


class TOTPLoginView(TemplateView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication using TOTP.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name: str = "authentication/login_totp.html"
    #: The user who tries to authenticate
    user: User | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Get revision context data

        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)

        if TYPE_CHECKING:
            assert self.user
        context["can_use_webauthn"] = self.user.fido_keys.exists()
        return context

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Check whether TOTP login can be used right now

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: Redirection to login form or region selection
        """

        if request.user.is_authenticated:
            return redirect("public:region_selection")

        if "mfa_user_id" not in request.session:
            return redirect("public:login")

        self.user = get_user_model().objects.get(id=request.session["mfa_user_id"])

        if not self.user.totp_key:
            return redirect("public:login")

        # Now process dispatch as it otherwise normally would
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Retrieves the entered TOTP code of the user and validates it.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: Redirection to region selection or rendered login form
        """
        if TYPE_CHECKING:
            assert self.user
        user_totp = request.POST.get("totp_code")

        if check_totp_code(user_totp, self.user.totp_key):
            auth_login(
                request, self.user, backend="django.contrib.auth.backends.ModelBackend"
            )
            return redirect("public:region_selection")

        messages.error(request, __(_("Login failed."), _("Please try again.")))
        return render(request, self.template_name, self.get_context_data(**kwargs))
