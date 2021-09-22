"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""
from cms.models import Region


def region_slug_processor(request):
    """
    This context processor retrieves the current ``region`` parameter and passes it to the templates.
    Additionally, the ``other_regions``-variable contains all other regions which are available via quick access.
    Usually, these are the regions configured in each user's profile, but if there are none set, we just list all
    available regions, ordered by the ``last_updated`` attribute.

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: The current region and other quick access regions
    :rtype: dict
    """
    current_region = Region.get_current_region(request)
    if request.user.is_authenticated and request.user.regions.exists():
        other_regions = request.user.regions
    else:
        other_regions = Region.objects
    if current_region:
        other_regions = other_regions.exclude(slug=current_region.slug)
    return {
        "other_regions": other_regions.order_by("-last_updated")[:10],
        "region": current_region,
    }
