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
from ...models import Organization
from .organization_content_mixin import OrganizationContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_organization"), name="dispatch")
class OrganizationListView(TemplateView, OrganizationContextMixin):
    """
    View for listing organizations (either non-archived or archived organizations depending on
    :attr:`~integreat_cms.cms.views.organizations.organization_list_view.OrganizationListView.archived`)
    """

    #: Template for list of non-archived organizations
    template_name = "organizations/organization_list.html"
    #: Whether or not to show archived organizations
    archived = False

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render organizations list for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        query = None

        organizations = Organization.objects.filter(
            region=region,
            archived=self.archived,
        )

        archived_count = Organization.objects.filter(
            region=region,
            archived=True,
        ).count()

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            organization_keys = Organization.search(region, query).values("pk")
            organizations = organizations.filter(pk__in=organization_keys)

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        paginator = Paginator(
            organizations,
            chunk_size,
        )
        chunk = request.GET.get("page")
        organization_chunk = paginator.get_page(chunk)

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
                "search_query": query,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Apply the query and filter the rendered organizations

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
