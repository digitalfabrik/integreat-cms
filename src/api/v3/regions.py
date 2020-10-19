"""
Views to return JSON representations of regions
"""
from django.db.models import Exists, OuterRef
from django.http import JsonResponse, HttpResponse

from cms.models import Region, Offer, Language
from cms.constants import region_status


def transform_region(region):
    """
    Function to create a JSON from a single region object, including information if region is live/ative.

    :param page_translation: single region object
    :type page_translation: ~cms.models.regions.region.Region

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

    :param page_translation: single region object
    :type page_translation: ~cms.models.regions.region.Region

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


def regions(_):
    """
    List all regions that are not archived and transform result into JSON

    :param _: not used Django request
    :type _: ~django.http.HttpRequest

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


def liveregions(_):
    """
    List all regions that are not archived and transform result into JSON

    :param _: not used Django request
    :type _: ~django.http.HttpRequest

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


def hiddenregions(_):
    """
    List all regions that are hidden and transform result into JSON

    :param _: not used Django request
    :type _: ~django.http.HttpRequest

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


def pushnew(_):
    """
    This is a magic black box convenience function for development. There is no
    reason for it, but we like it. As we do not care about randomly generated languages
    and it only consumes a few bytes of disk space, there is also no need to remove.
    And as non-profit projects rarely generate little money, this also does not pose a
    problem.

    :param _: not used Django request
    :type _: ~django.http.HttpRequest

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
    return HttpResponse("Pushing successful")
