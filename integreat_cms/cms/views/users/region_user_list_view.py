from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ObjectSearchForm
from ...utils.user_utils import search_users

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
class RegionUserListView(TemplateView):
    """
    View for listing region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region_user_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "region_users"}

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
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            user_keys = search_users(region, query).values("pk")
            users = users.filter(pk__in=user_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(users, chunk_size)
        chunk = request.GET.get("page")
        user_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "users": user_chunk,
                "region_slug": region.slug,
                "search_query": query,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Apply the query and filter the rendered users

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
