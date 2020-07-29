"""
Context processors pass additional variables to templates (see :ref:`context-processors`).
"""
from cms.models import Region


def region_slug_processor(request):
    """
    This context processor retrieves the current ``region`` parameter and passes it to the templates.
    Additionally, the ``regions``-variable contains all other regions except the current region
    (If there is no current region, it contains all regions).

    :param request: The current http request
    :type request: ~django.http.HttpRequest

    :return: The current region and all other regions
    :rtype: dict
    """
    region = Region.get_current_region(request)
    if region:
        regions = Region.objects.exclude(slug=region.slug)
    else:
        regions = Region.objects.all()
    return {'regions': regions, 'region': region}
