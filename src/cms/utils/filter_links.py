from django.db.models import Q

from linkcheck.models import Link


def filter_links(region_slug):
    """
    First filters links by current region
    Then filters by the link state
    Finally returns resulting query sets

    :param region_slug: the current regions slug
    :type region_slug: str
    :return: dictionary of filtered querysets
    :rtype: dict
    """
    qset = Link.objects.filter(
        Q(page_translations__page__region__slug=region_slug)
        | Q(event_translations__event__region__slug=region_slug)
        | Q(poi_translations__poi__region__slug=region_slug)
    )
    qset = qset.order_by("-url__last_checked")

    qset = list(
        filter(
            lambda link: (link.content_object.latest_revision == link.content_object),
            qset,
        )
    )

    valid_links = list(filter(lambda link: (not link.ignore and link.url.status), qset))
    unchecked_links = list(
        filter(lambda link: (not link.ignore and link.url.last_checked is None), qset)
    )
    ignored_links = list(filter(lambda link: (link.ignore), qset))
    invalid_links = list(
        filter(lambda link: (not link.ignore and not link.url.status), qset)
    )
    return {
        "all_links": qset,
        "valid_links": valid_links,
        "unchecked_links": unchecked_links,
        "ignored_links": ignored_links,
        "invalid_links": invalid_links,
    }
