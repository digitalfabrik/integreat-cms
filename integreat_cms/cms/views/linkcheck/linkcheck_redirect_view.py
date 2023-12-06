from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.shortcuts import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView

from ...decorators import permission_required

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_broken_links"), name="dispatch")
class LinkcheckRedirectView(RedirectView):
    """
    View for redirecting to main page of the broken link checker
    """

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Retrieve url for redirection

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: url to redirect to
        """
        kwargs.update({"url_filter": "invalid"})
        return reverse("linkcheck", kwargs=kwargs)
