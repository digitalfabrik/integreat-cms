from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View

from ...decorators import permission_required
from ...utils.linkcheck_utils import get_url_count

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_broken_links"), name="dispatch")
class LinkcheckStatsView(View):
    """
    Return the linkcheck counter stats
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Retrieve the stats about valid/invalid/unchecked/ignored links

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        # Link count
        count_dict = get_url_count(kwargs.get("region_slug"))
        return JsonResponse(count_dict)
