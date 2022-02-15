"""
This module contains all views related to multi-factor authentication
"""
import logging

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ....decorators import modify_mfa_authenticated

logger = logging.getLogger(__name__)


@method_decorator(modify_mfa_authenticated, name="dispatch")
class DeleteUserMfaKeyView(TemplateView):
    """
    View to delete a multi-factor-authentication key
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/delete.html"

    def get(self, request, *args, **kwargs):
        r"""
        Render mfa-deletion view

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        key = request.user.mfa_keys.get(id=kwargs["key_id"])

        if request.user.mfa_keys.count() == 1:
            messages.warning(
                request,
                _(
                    "This is your last key, once removed you will be able to log in without a second factor."
                ),
            )
        else:
            messages.warning(
                request,
                " ".join(
                    [
                        _(
                            "Once you remove the key you will need to use one of the other available keys to log into your account."
                        ),
                        _(
                            "Please make sure that you have at least one extra key available to log in before removing this key."
                        ),
                    ]
                ),
            )

        return render(
            request,
            self.template_name,
            {"key": key},
        )

    def post(self, request, **kwargs):
        r"""
        Delete a multi-factor-authentication key

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: A redirection to the user settings
        :rtype: ~django.http.HttpResponseRedirect
        """

        key = request.user.mfa_keys.get(id=kwargs["key_id"])
        messages.success(
            request,
            _('The 2-factor authentication key "{}" was successfully deleted').format(
                key.name
            ),
        )
        key.delete()
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        return redirect("user_settings", **kwargs)
