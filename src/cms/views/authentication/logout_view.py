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
        messages.info(request, _("You have been successfully logged off."))
        return super().dispatch(request, *args, **kwargs)
