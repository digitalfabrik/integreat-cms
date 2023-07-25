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
        request.available_regions = self.get_available_regions(request)
        request.region_selection = self.get_region_selection(
            request, request.available_regions
        )
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
        if region_slug := resolver_match.kwargs.get("region_slug"):
            return get_object_or_404(Region, slug=region_slug)
        return None

    @staticmethod
    def get_available_regions(request):
        """
        This method returns the regions available to the user based on the current request.

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :return: The regions available to the user of this request
        :rtype: list [ ~integreat_cms.cms.models.regions.region.Region ]
        """
        # If user isn't authenticated, don't provide any regions
        if not request.user.is_authenticated:
            return []
        # Firstly, attempt to provide the regions based on the user's settings
        # (the regions should already have been prefetched by the custom user manager)
        regions = request.user.regions.all()
        # If the user isn't a staff member or provided a valid list of regions, return those regions
        if (
            not request.user.is_superuser
            or not request.user.is_staff
            or len(regions) > 0
        ):
            return regions
        # As a last resort, query the most recently updated regions from the database
        # (this is only relevant for staff members without preferred regions)
        regions = Region.objects.order_by("-last_updated")
        return regions

    @staticmethod
    def get_region_selection(request, precomputed_all_regions=None):
        """
        This method returns the current region selection based on the current request.

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :param precomputed_all_regions: Regions available to the user (if get_available_regions was called anyway)
        :type precomputed_all_regions: list [ ~integreat_cms.cms.models.regions.region.Region ]

        :return: The current region selection of this request
        :rtype: list [ ~integreat_cms.cms.models.regions.region.Region ]
        """
        if precomputed_all_regions is None:
            precomputed_all_regions = RegionMiddleware.get_available_regions(request)
        # limit to 10 regions for the quick selection
        region_selection = list(precomputed_all_regions)[:10]
        if request.region:
            try:
                region_selection.remove(request.region)
            except ValueError:
                pass
        return region_selection
