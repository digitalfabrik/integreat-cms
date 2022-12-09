from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


from ...utils.totp_utils import check_totp_code
from ...utils.translation_utils import gettext_many_lazy as __


class TOTPLoginView(TemplateView):
    """
    View to extend the default login behavior from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication using TOTP.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/totp_login.html"
    #: The user who tries to authenticate
    user = None

    def dispatch(self, request, *args, **kwargs):
        r"""
        Check whether TOTP login can be used right now

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: Redirection to login form or region selection
        :rtype: ~django.http.HttpResponseRedirect
        """

        if request.user.is_authenticated:
            return redirect("public:region_selection")

        if "mfa_user_id" not in request.session:
            return redirect("public:login")

        self.user = get_user_model().objects.get(id=request.session["mfa_user_id"])

        if not self.user.totp_key:
            return redirect("public:login")

        # Now process dispatch as it otherwise normally would
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        r"""
        Retrieves the entered TOTP code of the user and validates it.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: Redirection to region selection or rendered login form
        :rtype: ~django.http.HttpResponseRedirect
        """

        user_totp = request.POST.get("totp_code")

        if check_totp_code(user_totp, self.user.totp_key):
            auth_login(
                request, self.user, backend="django.contrib.auth.backends.ModelBackend"
            )
            return redirect("public:region_selection")

        messages.error(request, __(_("Login failed."), _("Please try again.")))
        return render(request, self.template_name)
