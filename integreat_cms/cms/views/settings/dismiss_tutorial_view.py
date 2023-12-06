from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import HttpRequest, JsonResponse
from django.views.generic.base import View

if TYPE_CHECKING:
    from typing import Any


class DismissTutorial(View):
    """
    View to mark a tutorial dismissed for the current user.
    If it was marked dismissed it should not be shown again automatically.
    """

    #: The list of HTTP method names that this view will accept.
    #: Since this changes the database, we want to have the csrf protection of post views.
    http_method_names = ["post"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        r"""
        Marks a tutorial as dismissed

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        if (tutorial_slug := kwargs.get("slug")) == "page-tree":
            request.user.page_tree_tutorial_seen = True
        else:
            return JsonResponse(
                {"error": f"Tutorial '{tutorial_slug}' not found."}, status=404
            )

        request.user.save()

        return JsonResponse({"success": f"Tutorial '{tutorial_slug}' was dismissed."})
