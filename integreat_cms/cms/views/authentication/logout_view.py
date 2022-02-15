import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.utils.translation import ugettext as _

logger = logging.getLogger(__name__)


class LogoutView(auth_views.LogoutView):
    """
    View to log off a user
    """

    def dispatch(self, request, *args, **kwargs):
        r"""
        This function sends message, if logout was successful

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: passes form to dispatch function
        :rtype: ~django.http.HttpResponse
        """
        messages.info(request, _("You have been successfully logged off."))
        return super().dispatch(request, *args, **kwargs)
