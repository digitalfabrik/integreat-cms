"""
This module contains all views related to multi-factor authentication
"""
import logging
import time

from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from ....forms import AuthenticationForm

logger = logging.getLogger(__name__)


class AuthenticateModifyMfaView(FormView):
    """
    View to authenticate a user before changing the mfa settings
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "settings/mfa/authenticate.html"
    #: The form class for this form view (see :class:`~django.views.generic.edit.FormMixin`)
    form_class = AuthenticationForm

    def get_success_url(self):
        """
        Determine the URL to redirect to when the user is authenticated successfully

        :return: The url to redirect on success
        :rtype: str
        """
        kwargs = (
            {"region_slug": self.request.region.slug} if self.request.region else {}
        )
        return reverse("register_new_mfa_key", kwargs=kwargs)

    def form_valid(self, form):
        """
        This function overwrites :meth:`~django.views.generic.edit.FormMixin.form_valid` which is called if the
        :class:`~integreat_cms.cms.forms.users.authentication_form.AuthenticationForm` is valid. In case the user provided correct credentials,
        the current time is saved in a session variable so a timeout of the authentication can be implemented.

        :param form: Authentication form
        :type form: ~integreat_cms.cms.forms.users.authentication_form.AuthenticationForm

        :return: Redirect user to mfa login view or to :attr:`~integreat_cms.core.settings.LOGIN_REDIRECT_URL`
        :rtype: ~django.http.HttpResponseRedirect
        """
        if check_password(form.cleaned_data["password"], self.request.user.password):
            self.request.session["modify_mfa_authentication_time"] = time.time()
            if "mfa_redirect_url" in self.request.session:
                return redirect(self.request.session["mfa_redirect_url"])
            return super().form_valid(form)
        form.add_error("password", _("The provided password is not correct"))
        return super().form_invalid(form)
