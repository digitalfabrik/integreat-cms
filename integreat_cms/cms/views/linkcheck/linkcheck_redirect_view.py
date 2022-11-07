import logging

from django.shortcuts import reverse
from django.views.generic.base import RedirectView
from django.utils.decorators import method_decorator
from ...decorators import permission_required

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_broken_links"), name="dispatch")
class LinkcheckRedirectView(RedirectView):
    """
    View for redirecting to main page of the broken link checker
    """

    def get_redirect_url(self, *args, **kwargs):
        r"""
        Retrieve url for redirection

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: url to redirect to
        :rtype: str
        """
        kwargs.update({"url_filter": "invalid"})
        return reverse("linkcheck", kwargs=kwargs)
