from django.contrib import messages
from django.utils.translation import gettext as _

from ..form_views import CustomUpdateView
from ...forms import RegionForm


class RegionUpdateView(CustomUpdateView):
    """
    View for updating regions
    """

    #: The form class for this update view
    form_class = RegionForm

    def get(self, request, *args, **kwargs):
        r"""
        Render region form for HTTP GET requests

        :param request: The current request
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # Populate self.object
        response = super().get(request, *args, **kwargs)
        # Show warning when locations are enabled without bounding box
        if self.object.locations_enabled and not self.object.has_bounding_box:
            messages.warning(
                request,
                _(
                    "Locations are enabled but the bounding box coordinates are incomplete."
                ),
            )
        return response
