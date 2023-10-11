from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import modify_mfa_authenticated

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class TOTPDeleteView(TemplateView):
    """
    View to delete the TOTP key and disconnect authenticators.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/delete_totp.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render confirmation view for TOTP deletion

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        return render(
            request,
            self.template_name,
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Delete the TOTP key of an user.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: A redirection to the account settings
        """

        user = request.user

        user.totp_key = None
        user.save()
        messages.success(
            request,
            _(
                "You have successfully disconnected your account from your authenticator app."
            ),
        )
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        return redirect("user_settings", **kwargs)
