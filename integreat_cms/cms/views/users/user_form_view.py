from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import UserForm
from ...utils.welcome_mail_utils import send_welcome_mail

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_user"), name="dispatch")
@method_decorator(permission_required("cms.change_user"), name="post")
class UserFormView(TemplateView):
    """
    View for the user form and user form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "users/user_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "user_form"}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.users.user_form.UserForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        user = get_user_model().objects.filter(id=kwargs.get("user_id")).first()

        user_form = UserForm(instance=user)

        if user and not user.is_active:
            messages.info(request, _("Pending account activation"))

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "user_form": user_form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.users.user_form.UserForm` and save :class:`~integreat_cms.cms.models.users.user.User`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        user_instance = (
            get_user_model().objects.filter(id=kwargs.get("user_id")).first()
        )

        user_form = UserForm(data=request.POST, instance=user_instance)

        if not user_form.is_valid():
            # Add error messages
            user_form.add_error_messages(request)
        elif not (
            user_form.cleaned_data["is_superuser"]
            or user_form.cleaned_data["is_staff"]
            or user_form.cleaned_data["regions"]
        ):
            # Add error message
            messages.error(
                request,
                _(
                    "An account has to be either staff/superuser or needs to be restricted to at least one region."
                ),
            )
        elif not request.user.is_superuser and "is_superuser" in user_form.changed_data:
            messages.error(
                request,
                _("Superuser permissions need to be set by another superuser."),
            )
        elif (
            not request.user.is_superuser
            and "passwordless_authentication_enabled" in user_form.changed_data
        ):
            messages.error(
                request,
                _("Only superusers can enable or disable passwordless authentication."),
            )
        elif not user_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save forms
            user_form.save()
            # Check if user was created
            if not user_instance:
                # Send activation link or welcome mail
                activation = user_form.cleaned_data.get("send_activation_link")
                send_welcome_mail(request, user_form.instance, activation)
                # Add the success message and redirect to the edit page
                messages.success(
                    request,
                    _('Account "{}" was successfully created.').format(
                        user_form.instance.full_user_name
                    ),
                )
            else:
                # Add the success message
                messages.success(
                    request,
                    _('Account "{}" was successfully saved.').format(
                        user_form.instance.full_user_name
                    ),
                )
            return redirect(
                "edit_user",
                user_id=user_form.instance.id,
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "user_form": user_form,
            },
        )
