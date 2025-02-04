"""
This module contains all views related to multi-factor authentication
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ....decorators import modify_mfa_authenticated
from ....utils.translation_utils import gettext_many_lazy as __

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class DeleteUserFidoKeyView(TemplateView):
    """
    View to delete a multi-factor-authentication key
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/delete.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render mfa-deletion view

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        key = request.user.fido_keys.get(id=kwargs["key_id"])

        if request.user.fido_keys.count() == 1:
            messages.warning(
                request,
                _(
                    "This is your last key, once removed you will be able to log in without a second factor.",
                ),
            )
        else:
            messages.warning(
                request,
                __(
                    _(
                        "Once you remove the key you will need to use one of the other available keys to log into your account.",
                    ),
                    _(
                        "Please make sure that you have at least one extra key available to log in before removing this key.",
                    ),
                ),
            )

        return render(
            request,
            self.template_name,
            {"key": key},
        )

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponseRedirect:
        r"""
        Delete a multi-factor-authentication key

        :param request: The current request
        :param \**kwargs: The supplied keyword arguments
        :return: A redirection to the account settings
        """

        key = request.user.fido_keys.get(id=kwargs["key_id"])
        messages.success(
            request,
            _('The 2-factor authentication key "{}" was successfully deleted').format(
                key.name,
            ),
        )
        key.delete()
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        return redirect("user_settings", **kwargs)
