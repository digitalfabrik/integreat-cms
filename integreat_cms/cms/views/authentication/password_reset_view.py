from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...forms import CustomPasswordResetForm
from ...utils.translation_utils import gettext_many_lazy as __

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect
    from django.template.response import TemplateResponse


logger = logging.getLogger(__name__)


class PasswordResetView(auth_views.PasswordResetView):
    """
    View to extend the default login behaviour from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: The template which should be rendered
    template_name = "authentication/password_reset_form.html"
    #: The full name of a template to use for generating the email with the reset password link.
    email_template_name = "emails/password_reset_email.txt"
    #: The full name of a template to use for generating the html email with the reset password link.
    html_email_template_name = "emails/password_reset_email.html"
    #: If the password reset process was successfully initialized, stay on the password reset page
    success_url = reverse_lazy("public:password_reset")
    #: The form for the password reset
    form_class = CustomPasswordResetForm

    def dispatch(
        self, *args: HttpRequest, **kwargs: Any
    ) -> HttpResponseRedirect | TemplateResponse:
        r"""
        The view part of the view. Handles all HTTP methods equally.

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response or a redirection
        """
        if self.request.user.is_authenticated:
            messages.success(
                self.request,
                _("You are already logged in."),
            )
            return redirect("public:region_selection")
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form: CustomPasswordResetForm) -> HttpResponseRedirect:
        """
        This function validates the form and sends a message depending if the function was executed successfully

        :param form: The supplied form
        :return: passes form to form validation
        """
        logger.debug(
            "A password reset link for email %r was requested.",
            form.cleaned_data["email"],
        )
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                __(
                    _(
                        "We've emailed you instructions for setting your password, if an account exists with the email you entered."
                    ),
                    _("You should receive them shortly."),
                    _(
                        "If you don’t receive an email, please make sure you’ve entered the address you registered with, and check your spam folder."
                    ),
                ),
            )
            return response
        except RuntimeError as e:
            messages.error(
                self.request,
                __(
                    _("An error occurred! Could not send {}.").format(
                        _("password reset email")
                    ),
                    e,
                ),
            )
            return redirect("public:password_reset")
