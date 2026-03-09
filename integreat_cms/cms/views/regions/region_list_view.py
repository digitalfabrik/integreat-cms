from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models import Region
from ..mixins import FilterSortMixin, PaginationMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_region"), name="dispatch")
class RegionListView(TemplateView, FilterSortMixin, PaginationMixin):
    """
    View for listing regions
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "regions/region_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "regions"}
    model = Region

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render region list

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        regions = Region.objects.all()
        search_query = request.GET.get("search_query") or None

        regions = self.get_filtered_sorted_queryset(regions)
        region_chunk = self.paginate_queryset(regions)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "regions": region_chunk,
                "search_query": search_query,
            },
        )
