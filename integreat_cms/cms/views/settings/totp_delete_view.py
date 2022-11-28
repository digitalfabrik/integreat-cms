import logging
from django.shortcuts import redirect, render

from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import TemplateView


from ...decorators import modify_mfa_authenticated

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class TOTPDeleteView(TemplateView):
    """
    View to delete the TOTP key and disconnect authenticators.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/delete_totp.html"

    def get(self, request, *args, **kwargs):
        r"""
        Render confirmation view for TOTP deletion

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        return render(
            request,
            self.template_name,
        )

    def post(self, request, *args, **kwargs):
        r"""
        Delete the TOTP key of an user.

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: A redirection to the account settings
        :rtype: ~django.http.HttpResponseRedirect
        """

        user = request.user

        user.totp_key = None
        user.save()
        messages.success(
            request,
            _(
                "You have successfully disconnected your account from your authenticator app."
            ),
        )
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        return redirect("user_settings", **kwargs)
