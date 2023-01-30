import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...forms import UserEmailForm, UserPasswordForm, UserPreferencesForm

logger = logging.getLogger(__name__)


class UserSettingsView(TemplateView):
    """
    View for the individual account settings
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/user_settings.html"

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "keys": self.request.user.mfa_keys.all(),
                "user_email_form": UserEmailForm(instance=self.request.user),
                "user_password_form": UserPasswordForm(instance=self.request.user),
                "user_preferences_form": UserPreferencesForm(
                    instance=self.request.user
                ),
            }
        )
        return context

    # pylint: disable=unused-argument, too-many-branches
    def post(self, request, *args, **kwargs):
        r"""
        Submit :class:`~integreat_cms.cms.forms.users.user_email_form.UserEmailForm` and
        :class:`~integreat_cms.cms.forms.users.user_password_form.UserPasswordForm` and save :class:`~django.contrib.auth.models.User`
        object

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
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
