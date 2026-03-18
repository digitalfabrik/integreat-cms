from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models import Organization
from ..mixins import FilterSortMixin, PaginationMixin
from .organization_content_mixin import OrganizationContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_organization"), name="dispatch")
class OrganizationListView(
    TemplateView, OrganizationContextMixin, FilterSortMixin, PaginationMixin
):
    """
    View for listing organizations (either non-archived or archived organizations depending on
    :attr:`~integreat_cms.cms.views.organizations.organization_list_view.OrganizationListView.archived`)
    """

    #: Template for list of non-archived organizations
    template_name = "organizations/organization_list.html"
    #: Whether or not to show archived organizations
    archived = False
    model = Organization

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render organizations list for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        search_query = request.GET.get("search_query") or None

        organizations = Organization.objects.filter(
            region=region,
            archived=self.archived,
        )

        archived_count = Organization.objects.filter(
            region=region,
            archived=True,
        ).count()

        organizations = self.get_filtered_sorted_queryset(organizations)
        organization_chunk = self.paginate_queryset(organizations)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "region_slug": region.slug,
                "is_archive": self.archived,
                "organizations": organization_chunk,
                "archived_count": archived_count,
                "current_menu_item": "organizations",
                "search_query": search_query,
            },
        )
