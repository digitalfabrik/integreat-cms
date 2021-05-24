from django.db.models import Q

from linkcheck.models import Link


def filter_links(region_slug):
    """[summary]

    :param region_slug: [description]
    :type region_slug: [type]
    :return: [description]
    :rtype: [type]
    """
    qset = Link.objects.filter(
        Q(page_translations__page__region__slug=region_slug)
        | Q(event_translations__event__region__slug=region_slug)
        | Q(poi_translations__poi__region__slug=region_slug)
    )
    qset = qset.order_by("-url__last_checked")
    valid_links = qset.filter(ignore=False, url__status__exact=True)
    unchecked_links = qset.filter(ignore=False, url__last_checked__exact=None)
    ignored_links = qset.filter(ignore=True)
    invalid_links = qset.filter(ignore=False, url__status__exact=False)
    return {
        "all_links": qset,
        "valid_links": valid_links,
        "unchecked_links": unchecked_links,
        "ignored_links": ignored_links,
        "invalid_links": invalid_links,
    }
