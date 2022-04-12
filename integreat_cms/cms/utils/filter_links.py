from ..models import PageTranslation, EventTranslation, POITranslation


def filter_links(region_slug, link_filter=None):
    """
    Filter all links of one region by the given category

    :param region_slug: the current regions slug
    :type region_slug: str

    :param link_filter: which links should be returned (one of ``valid``, ``invalid``, ``ignored``, ``unchecked``).
                        If parameter is not in these choices or omitted, all links are returned by default.
    :type link_filter: str

    :return: a tuple of the requested links and a dict containing the counters of all remaining links
    :rtype: tuple
    """
    # Get all translation objects of this region and prefetch its links
    page_translations = list(
        PageTranslation.objects.filter(page__region__slug=region_slug)
        .distinct("page", "language")
        .select_related("language")
        .prefetch_related("links__url")
    )
    event_translations = list(
        EventTranslation.objects.filter(event__region__slug=region_slug)
        .distinct("event", "language")
        .select_related("language")
        .prefetch_related("links__url")
    )
    poi_translations = list(
        POITranslation.objects.filter(poi__region__slug=region_slug)
        .distinct("poi", "language")
        .select_related("language")
        .prefetch_related("links__url")
    )
    # Filter out translations with no links
    translations = list(
        filter(
            lambda translation: translation.links,
            page_translations + event_translations + poi_translations,
        )
    )
    # Convert translations to list of dicts to enable filtering of links in python
    links = [
        {"translation": translation, "link": link}
        for translation in translations
        for link in translation.links.all()
    ]
    # Split link lists into their respective categories
    ignored_links, valid_links, invalid_links, unchecked_links = [], [], [], []
    for item in links:
        if item["link"].ignore:
            ignored_links.append(item)
        elif item["link"].url.status:
            valid_links.append(item)
        elif item["link"].url.last_checked:
            invalid_links.append(item)
        else:
            unchecked_links.append(item)
    # Pass the number of links to a dict which can be used as extra template context
    count_dict = {
        "number_all_links": len(links),
        "number_valid_links": len(valid_links),
        "number_unchecked_links": len(unchecked_links),
        "number_ignored_links": len(ignored_links),
        "number_invalid_links": len(invalid_links),
    }
    # Return the requested links
    if link_filter == "valid":
        links = valid_links
    elif link_filter == "unchecked":
        links = unchecked_links
    elif link_filter == "ignored":
        links = ignored_links
    elif link_filter == "invalid":
        links = invalid_links
    return links, count_dict
