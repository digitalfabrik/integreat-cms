from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


class ApiTokenDeleteView(View):
    """
    View to delete a personal API token
    """

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponseRedirect:
        r"""
        Delete the given API token of the current user

        The queryset is restricted to the tokens of the requesting user, so a user can never
        delete a token of somebody else.

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: A redirection to the user settings
        """
        token = get_object_or_404(request.user.api_tokens, id=kwargs["token_id"])
        logger.info("%r deleted %r", request.user, token)
        token.delete()
        messages.success(request, _("API token was successfully deleted"))

        redirect_kwargs = {"region_slug": request.region.slug} if request.region else {}
        return redirect("user_settings", **redirect_kwargs)
