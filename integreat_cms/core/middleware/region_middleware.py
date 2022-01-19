import logging
from django.shortcuts import get_object_or_404
from django.urls import resolve

from ...cms.models import Region

logger = logging.getLogger(__name__)


class RegionMiddleware:
    """
    Middleware class that adds the current region to the request variable
    """

    def __init__(self, get_response):
        """
        Initialize the middleware for the current view

        :param get_response: A callable to get the response for the current request
        :type get_response: ~collections.abc.Callable
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Call the middleware for the current request

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :return: The response after the region has been added to the request variable
        :rtype: ~django.http.HttpResponse
        """
        request.region = self.get_current_region(request)
        request.region_selection = self.get_region_selection(request)
        return self.get_response(request)

    @staticmethod
    def get_current_region(request):
        """
        This method returns the current region based on the current request.

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :raises ~django.http.Http404: When the current request has a ``region_slug`` parameter, but there is no region
                                      with that slug.

        :return: The current region of this request
        :rtype: ~integreat_cms.cms.models.regions.region.Region
        """
        # Resolve current url
        resolver_match = resolve(request.path)
        region_slug = resolver_match.kwargs.get("region_slug")
        if not region_slug:
            return None
        return get_object_or_404(Region, slug=region_slug)

    @staticmethod
    def get_region_selection(request):
        """
        This method returns the current region selection based on the current request.

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :return: The current region selection of this request
        :rtype: list [ ~integreat_cms.cms.models.regions.region.Region ]
        """
        # If user isn't authenticated, don't provide a region selection
        if not request.user.is_authenticated:
            return []
        # Firstly, attempt to provide the region selection based on the user's settings
        # (the regions should already have been prefetched by the custom user manager)
        region_selection = list(request.user.regions.all())[:10]
        # Exclude the current region from the available options
        if request.region:
            try:
                region_selection.remove(request.region)
            except ValueError:
                pass
        # If the user isn't a staff member or provided a valid selection, return those regions
        if (
            not request.user.is_superuser
            or not request.user.is_staff
            or len(region_selection) > 0
        ):
            return region_selection
        # As a last resort, query the 10 most recently updated regions from the database
        # (this is only relevant for staff members without preferred regions)
        region_selection = Region.objects.order_by("-last_updated")
        if request.region:
            region_selection = region_selection.exclude(pk=request.region.pk)
        return region_selection[:10]
