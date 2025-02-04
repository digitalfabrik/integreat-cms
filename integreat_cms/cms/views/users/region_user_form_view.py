from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import RegionUserForm
from ...utils.welcome_mail_utils import send_welcome_mail

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
@method_decorator(permission_required("cms.change_user"), name="post")
class RegionUserFormView(TemplateView):
    """
    View for the user form of region users
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/region_user_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "region_user_form"}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.users.user_form.UserForm` for region users

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region

        # filter region users to make sure no users from other regions can be changed through this view
        user = region.region_users.filter(id=kwargs.get("user_id")).first()

        region_user_form = RegionUserForm(region=region, instance=user)

        if user and not user.is_active:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "user_form": region_user_form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.users.user_form.UserForm` and  save :class:`~django.contrib.auth.models.User`
        object for region users

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        region = request.region

        # filter region users to make sure no users from other regions can be changed through this view
        user_instance = region.region_users.filter(id=kwargs.get("user_id")).first()

        region_user_form = RegionUserForm(
            region=region,
            data=request.POST,
            instance=user_instance,
        )

        if not region_user_form.is_valid():
            # Add error messages
            region_user_form.add_error_messages(request)
        elif not region_user_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save forms
            region_user_form.save()
            region_user_form.instance.regions.add(region)
            region_user_form.save()
            # Check if user was created
            if not user_instance:
                # Send activation link or welcome mail
                activation = region_user_form.cleaned_data.get("send_activation_link")
                send_welcome_mail(request, region_user_form.instance, activation)
                # Add the success message and redirect to the edit page
                messages.success(
                    request,
                    _('Account "{}" was successfully created.').format(
                        region_user_form.instance.full_user_name,
                    ),
                )
            else:
                # Add the success message
                messages.success(
                    request,
                    _('Account "{}" was successfully saved.').format(
                        region_user_form.instance.full_user_name,
                    ),
                )
            return redirect(
                "edit_region_user",
                region_slug=region.slug,
                user_id=region_user_form.instance.id,
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "user_form": region_user_form,
            },
        )
