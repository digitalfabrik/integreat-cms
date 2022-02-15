import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    View to confirm that the password should be reset
    """

    #: The template which should be rendered
    template_name = "authentication/password_reset_confirm.html"
    #: If the password was successfully reset, redirect to the login
    success_url = reverse_lazy("public:login")

    def dispatch(self, *args, **kwargs):
        r"""
        The view part of the view. Handles all HTTP methods equally.

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response or a redirection to the password reset page
        :rtype: ~django.template.response.TemplateResponse or ~django.http.HttpResponseRedirect
        """
        if self.request.user.is_authenticated:
            messages.success(
                self.request,
                _("You are already logged in."),
            )
            return redirect("public:region_selection")
        response = super().dispatch(*args, **kwargs)
        if isinstance(response, HttpResponseRedirect) or self.validlink:
            # If the link is valid, render the password reset confirm form (redirect means valid because the first step
            # is to store the token in a session variable and redirect to the generic [...]-set-password/ url)
            return response
        # If not, redirect to the password reset form
        messages.error(
            self.request,
            " ".join(
                [
                    _("This password reset link is invalid."),
                    _("It may have already been used."),
                    _("Please request a new link to reset your password."),
                ]
            ),
        )
        logger.debug("An invalid password reset link was used.")
        return redirect("public:password_reset")

    def form_valid(self, form):
        """
        If the form is valid, show a success message.

        :param form: The supplied form
        :type form: ~django.contrib.auth.forms.SetPasswordForm

        :return: form validation
        :rtype: ~django.http.HttpResponse

        """
        messages.success(
            self.request,
            " ".join(
                [
                    _("Your password has been successfully changed."),
                    _("You can now log in with your new password."),
                ]
            ),
        )
        logger.info("The password for %r was changed.", form.user)
        return super().form_valid(form)
