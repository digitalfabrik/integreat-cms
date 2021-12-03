"""
Expansion of API-Endpoints for the CMS
"""
from django.conf.urls import include, url

from .v3.events import events
from .v3.feedback import (
    page_feedback,
    search_result_feedback,
    region_feedback,
    offer_feedback,
    offer_list_feedback,
    event_list_feedback,
    event_feedback,
    poi_feedback,
    map_feedback,
    imprint_page_feedback,
    legacy_feedback_endpoint,
)
from .v3.imprint import imprint
from .v3.languages import languages
from .v3.locations import locations
from .v3.pages import pages, children, parents, single_page
from .v3.pdf_export import pdf_export
from .v3.push_notifications import sent_push_notifications
from .v3.regions import regions, liveregions, hiddenregions
from .v3.offers import offers


#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "api"

content_api_urlpatterns = [
    url(r"^pages/?$", pages, name="pages"),
    url(r"^locations/?$", locations, name="locations"),
    url(r"^events/?$", events, name="events"),
    url(
        r"^(?:page|post)/?$",
        single_page,
        name="single_page",
    ),
    url(r"^children/?$", children, name="children"),
    url(r"^parents/?$", parents, name="parents"),
    url(
        r"^pdf/?$",
        pdf_export,
        name="pdf_export",
    ),
    url(
        r"^sent_push_notifications/?$",
        sent_push_notifications,
        name="sent_push_notifications",
    ),
    url(
        r"^(?:imprint|disclaimer)/?$",
        imprint,
        name="imprint",
    ),
    url(r"^(?:offers|extras)/?$", offers, name="offers"),
    url(
        r"^feedback/",
        include(
            [
                url(
                    r"^$",
                    legacy_feedback_endpoint.legacy_feedback_endpoint,
                    name="legacy_feedback_endpoint",
                ),
                url(
                    r"^categories/?$",
                    region_feedback.region_feedback,
                    name="region_feedback",
                ),
                url(
                    r"^page/?$",
                    page_feedback.page_feedback,
                    name="page_feedback",
                ),
                url(
                    r"^poi/?$",
                    poi_feedback.poi_feedback,
                    name="poi_feedback",
                ),
                url(
                    r"^event/?$",
                    event_feedback.event_feedback,
                    name="event_feedback",
                ),
                url(
                    r"^events/?$",
                    event_list_feedback.event_list_feedback,
                    name="event_list_feedback",
                ),
                url(
                    r"^imprint-page/?$",
                    imprint_page_feedback.imprint_page_feedback,
                    name="imprint_page_feedbacks",
                ),
                url(
                    r"^map/?$",
                    map_feedback.map_feedback,
                    name="map_feedback",
                ),
                url(
                    r"^search/?$",
                    search_result_feedback.search_result_feedback,
                    name="search_result_feedback",
                ),
                url(
                    r"^(?:extras|offers)/?$",
                    offer_list_feedback.offer_list_feedback,
                    name="offer_list_feedback",
                ),
                url(
                    r"^(?:extra|offer)/?$",
                    offer_feedback.offer_feedback,
                    name="offer_feedback",
                ),
            ]
        ),
    ),
]

region_api_urlpatterns = [
    url(r"^$", regions, name="regions"),
    url(r"^live/?$", liveregions, name="regions_live"),
    url(r"^hidden/?$", hiddenregions, name="regions_hidden"),
]

#: The url patterns of this module (see :doc:`topics/http/urls`)
urlpatterns = [
    url(r"^api/regions/", include(region_api_urlpatterns)),
    url(r"^wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
    url(
        r"^api/(?P<region_slug>[-\w]+)/",
        include(
            [
                url(r"^languages/?$", languages, name="languages"),
                url(r"^(?:offers|extras)/?$", offers, name="offers"),
                url(r"^(?P<language_slug>[-\w]+)/", include(content_api_urlpatterns)),
            ]
        ),
    ),
    url(
        r"^(?P<region_slug>[-\w]+)/",
        include(
            [
                url(
                    r"^de/wp-json/extensions/v3/languages/?$",
                    languages,
                    name="languages",
                ),
                url(
                    r"^(?P<language_slug>[-\w]+)/wp-json/extensions/v3/",
                    include(content_api_urlpatterns),
                ),
            ]
        ),
    ),
]
