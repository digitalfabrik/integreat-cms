from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class LogoutView(auth_views.LogoutView):
    """
    View to log off a user
    """

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        This function sends message, if logout was successful

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: passes form to dispatch function
        """
        messages.info(request, _("You have been successfully logged off."))
        return super().dispatch(request, *args, **kwargs)
