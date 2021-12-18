import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...models import Organization
from .organization_context_mixin import OrganizationContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_organization"), name="dispatch")
class OrganizationListView(TemplateView, OrganizationContextMixin):
    """
    View for listing organizations
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "organizations/organization_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "organizations"}

    def get(self, request, *args, **kwargs):
        r"""
        Render organization list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        organizations = Organization.objects.all()
        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(organizations.order_by("slug"), chunk_size)
        chunk = request.GET.get("page")
        organization_chunk = paginator.get_page(chunk)

        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {**self.base_context, **context, "organizations": organization_chunk},
        )
