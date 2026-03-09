from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models import User
from ..mixins import FilterSortMixin, PaginationMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
class RegionUserListView(TemplateView, FilterSortMixin, PaginationMixin):
    """
    View for listing region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region_user_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "region_users"}
    model = User

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render region user list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region

        users = (
            region.region_users.select_related("organization")
            .prefetch_related("groups__role")
            .order_by("username")
        )
        search_query = request.GET.get("search_query") or None

        users = self.get_filtered_sorted_queryset(users)
        user_chunk = self.paginate_queryset(users)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "users": user_chunk,
                "region_slug": region.slug,
                "search_query": search_query,
            },
        )
