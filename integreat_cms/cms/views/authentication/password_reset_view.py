import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.shortcuts import redirect

from ...forms import CustomPasswordResetForm

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

    def dispatch(self, *args, **kwargs):
        r"""
        The view part of the view. Handles all HTTP methods equally.

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response or a redirection
        :rtype: ~django.template.response.TemplateResponse or ~django.http.HttpResponseRedirect
        """
        if self.request.user.is_authenticated:
            messages.success(
                self.request,
                _("You are already logged in."),
            )
            return redirect("public:region_selection")
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        This function validates the form and sends a message depending if the function was executed successfully

        :param form: The supplied form
        :type form: ~django.contrib.auth.forms.SetPasswordForm

        :return: passes form to form validation
        :rtype: ~django.http.HttpResponse

        If the form is valid, show a success message.
        """
        messages.success(
            self.request,
            " ".join(
                [
                    _(
                        "We've emailed you instructions for setting your password, if an account exists with the email you entered."
                    ),
                    _("You should receive them shortly."),
                    _(
                        "If you don’t receive an email, please make sure you’ve entered the address you registered with, and check your spam folder."
                    ),
                ]
            ),
        )
        logger.debug(
            "A password reset link for email %r was requested.",
            form.cleaned_data["email"],
        )
        return super().form_valid(form)
