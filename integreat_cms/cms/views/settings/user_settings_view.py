from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...forms import UserEmailForm, UserPasswordForm, UserPreferencesForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


class UserSettingsView(TemplateView):
    """
    View for the individual account settings
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/user_settings.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :return: The template context
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "keys": self.request.user.fido_keys.all(),
                "user_email_form": UserEmailForm(instance=self.request.user),
                "user_password_form": UserPasswordForm(instance=self.request.user),
                "user_preferences_form": UserPreferencesForm(
                    instance=self.request.user
                ),
            }
        )
        return context

    def post(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Submit :class:`~integreat_cms.cms.forms.users.user_email_form.UserEmailForm` and
        :class:`~integreat_cms.cms.forms.users.user_password_form.UserPasswordForm` and save :class:`~django.contrib.auth.models.User`
        object

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region

        user = request.user

        if request.POST.get("submit_form") == "email_form":
            user_email_form = UserEmailForm(data=request.POST, instance=user)
            if not user_email_form.is_valid():
                user_email_form.add_error_messages(request)
                return render(
                    request,
                    self.template_name,
                    {
                        **self.get_context_data(**kwargs),
                        "user_email_form": user_email_form,
                    },
                )
            if not user_email_form.has_changed():
                messages.info(request, _("No changes made"))
            else:
                user_email_form.save()
                messages.success(request, _("E-mail-address was successfully saved"))

        elif request.POST.get("submit_form") == "password_form":
            user_password_form = UserPasswordForm(data=request.POST, instance=user)
            if not user_password_form.is_valid():
                user_password_form.add_error_messages(request)
                return render(
                    request,
                    self.template_name,
                    {
                        **self.get_context_data(**kwargs),
                        "user_password_form": user_password_form,
                    },
                )
            if not user_password_form.has_changed():
                messages.info(request, _("No changes made"))
            else:
                user = user_password_form.save()
                # Prevent user from being logged out after password has changed
                update_session_auth_hash(request, user)
                messages.success(request, _("Password was successfully saved"))

        elif request.POST.get("submit_form") == "preferences_form":
            user_preferences_form = UserPreferencesForm(
                data=request.POST, instance=user
            )
            if not user_preferences_form.is_valid():
                user_preferences_form.add_error_messages(request)
                return render(
                    request,
                    self.template_name,
                    {
                        **self.get_context_data(**kwargs),
                        "user_preferences_form": user_preferences_form,
                    },
                )
            if not user_preferences_form.has_changed():
                messages.info(request, _("No changes made"))
            else:
                user_preferences_form.save()
                messages.success(request, _("Preferences were successfully saved"))

        kwargs = {"region_slug": region.slug} if region else {}
        return redirect("user_settings", **kwargs)
