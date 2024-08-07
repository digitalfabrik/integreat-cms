from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import permission_required
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
    template = "organizations/organization_list.html"
    #: Template for list of archived organizations
    template_archived = "organizations/organization_list_archived.html"
    #: Whether or not to show archived organizations
    archived = False

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.organizations.organization_list_view.OrganizationListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """
        return self.template_archived if self.archived else self.template

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render organizations list for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region

        organization_slug = kwargs.get("slug")

        # Get the organization instance, or 404 if it doesn't exist
        organization = get_object_or_404(
            Organization, slug=organization_slug, region=region
        )
        archived_count = Organization.objects.filter(
            region=region, archived=True
        ).count()
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "region_slug": region.slug,
                "slug": organization.slug,
                "archived_count": archived_count,
            },
        )
