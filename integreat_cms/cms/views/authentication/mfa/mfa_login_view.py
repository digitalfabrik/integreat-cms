import logging

from django.contrib.auth import views as auth_views

logger = logging.getLogger(__name__)


class MfaLoginView(auth_views.LoginView):
    """
    View to extend the default login behaviour from :class:`~django.contrib.auth.views.LoginView` with
    multi-factor-authentication.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "authentication/login_mfa.html"
