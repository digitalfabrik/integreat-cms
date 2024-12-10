from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import OrganizationForm
from ...models import Organization
from ..media.media_context_mixin import MediaContextMixin
from .organization_content_mixin import OrganizationContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_organization"), name="dispatch")
@method_decorator(permission_required("cms.change_organization"), name="post")
class OrganizationFormView(TemplateView, OrganizationContextMixin, MediaContextMixin):
    """
    Class for rendering the organizations form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "organizations/organization_form.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render organization form for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region

        # get organization objects if it exists, otherwise objects are None
        organization_instance = region.organizations.filter(
            id=kwargs.get("organization_id"),
        ).first()

        if organization_instance and organization_instance.archived:
            disabled = True
            messages.warning(
                request,
                _("You cannot edit this organization because it is archived."),
            )
        elif not request.user.has_perm("cms.change_organization"):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit organizations."),
            )
        else:
            disabled = False

        organization_form = OrganizationForm(
            instance=organization_instance,
            disabled=disabled,
        )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": organization_form,
                "current_menu_item": "organizations",
            },
        )

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        r"""
        Save organization form for HTTP POST requests

        :param request: Object representing the user call
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region

        organization_instance = Organization.objects.filter(
            id=kwargs.get("organization_id"),
        ).first()

        if organization_instance and organization_instance.archived:
            return redirect(
                "edit_organization",
                **{
                    "region_slug": region.slug,
                    "organization_id": organization_instance.id,
                },
            )

        organization_form = OrganizationForm(
            data=request.POST,
            files=request.FILES,
            instance=organization_instance,
            additional_instance_attributes={
                "region": region,
            },
        )

        if organization_form.is_valid():
            organization_form.save()

            if not organization_instance:
                messages.success(
                    request,
                    _('Organization "{}" was successfully created').format(
                        organization_form.instance,
                    ),
                )
                return redirect(
                    "edit_organization",
                    **{
                        "region_slug": region.slug,
                        "organization_id": organization_form.instance.id,
                    },
                )

            messages.success(
                request,
                _('Organization "{}" was successfully saved').format(
                    organization_form.instance,
                ),
            )
        else:
            organization_form.add_error_messages(request)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": organization_form,
                "current_menu_item": "organizations",
            },
        )
