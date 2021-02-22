"""
Views to return JSON representations of regions
"""
from django.db.models import Exists, OuterRef
from django.http import JsonResponse

from cms.models import Region, Offer, Language
from cms.constants import region_status

from ..decorators import json_response


def transform_region(region):
    """
    Function to create a JSON from a single region object, including information if region is live/active.

    :param region: The region object which should be converted
    :type region: ~cms.models.regions.region.Region

    :return: return data necessary for API
    :rtype: dict
    """
    return {
        "id": region.id,
        "name": region.get_administrative_division_display() + " " + region.name,
        "path": region.slug,
        "live": region.status == region_status.ACTIVE,
        "prefix": region.get_administrative_division_display(),
        "name_without_prefix": region.name,
        "plz": region.postal_code,
        "extras": region.offers_enabled,
        "events": region.events_enabled,
        "push-notifications": region.push_notifications_enabled,
        "longitude": region.longitude,
        "latitude": region.latitude,
        "aliases": region.aliases,
    }


def transform_region_by_status(region):
    """
    Function to create a JSON from a single "active" region object.

    :param region: The region object which should be converted
    :type region: ~cms.models.regions.region.Region

    :return: return data necessary for API
    :rtype: dict
    """
    return {
        "id": region.id,
        "name": region.get_administrative_division_display() + " " + region.name,
        "path": region.slug,
        "prefix": region.get_administrative_division_display(),
        "name_without_prefix": region.name,
        "plz": region.postal_code,
        "offers": region.offers_enabled,
        "events": region.events_enabled,
        "push-notifications": region.push_notifications_enabled,
        "longitude": region.longitude,
        "latitude": region.latitude,
        "aliases": region.aliases,
    }


@json_response
def regions(_):
    """
    List all regions that are not archived and transform result into JSON

    :return: JSON object according to APIv3 regions endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    result = list(
        map(
            transform_region,
            Region.objects.exclude(status=region_status.ARCHIVED).annotate(
                offers_enabled=Exists(Offer.objects.filter(region=OuterRef("pk")))
            ),
        )
    )
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


@json_response
def liveregions(_):
    """
    List all regions that are not archived and transform result into JSON

    :return: JSON object according to APIv3 live regions endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    result = list(
        map(
            transform_region_by_status,
            Region.objects.filter(status=region_status.ACTIVE).annotate(
                offers_enabled=Exists(Offer.objects.filter(region=OuterRef("pk")))
            ),
        )
    )
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


@json_response
def hiddenregions(_):
    """
    List all regions that are hidden and transform result into JSON

    :return: JSON object according to APIv3 hidden regions endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    result = list(
        map(
            transform_region_by_status,
            Region.objects.filter(status=region_status.HIDDEN).annotate(
                offers_enabled=Exists(Offer.objects.filter(region=OuterRef("pk")))
            ),
        )
    )
    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays


@json_response
def pushnew(_):
    """
    This is a magic black box convenience function for development. There is no
    reason for it, but we like it. As we do not care about randomly generated languages
    and it only consumes a few bytes of disk space, there is also no need to remove.
    And as non-profit projects rarely generate little money, this also does not pose a
    problem.

    :return: All is right with the world
    :rtype: ~realms.magic.unicorn
    """
    de = Language(code="de", title="Deutsch", text_direction="ltr")
    dutch = Language(code="nl", title="Netherlands", text_direction="ltr")
    de.save()
    dutch.save()
    region = Region(
        title="Augsburg",
        name="augsburg",
        languages=[de, dutch],
        push_notification_channels=[],
    )
    region.save()
    return JsonResponse({"success": "Pushing successful"}, status=201)
