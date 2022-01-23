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

content_api_urlpatterns = [
    url(r"^pages/?$", pages, name="api_pages"),
    url(r"^locations/?$", locations, name="api_locations"),
    url(r"^events/?$", events, name="api_events"),
    url(
        r"^(?:page|post)/?$",
        single_page,
        name="api_single_page",
    ),
    url(r"^children/?$", children, name="api_children"),
    url(r"^parents/?$", parents, name="api_parents"),
    url(
        r"^pdf/?$",
        pdf_export,
        name="api_pdf_export",
    ),
    url(
        r"^sent_push_notifications/?$",
        sent_push_notifications,
        name="api_sent_push_notifications",
    ),
    url(
        r"^(?:imprint|disclaimer)/?$",
        imprint,
        name="api_imprint",
    ),
    url(r"^(?:offers|extras)/?$", offers, name="api_offers"),
    url(
        r"^feedback/",
        include(
            [
                url(
                    r"^$",
                    legacy_feedback_endpoint.legacy_feedback_endpoint,
                    name="api_legacy_feedback_endpoint",
                ),
                url(
                    r"^categories/?$",
                    region_feedback.region_feedback,
                    name="api_region_feedback",
                ),
                url(
                    r"^page/?$",
                    page_feedback.page_feedback,
                    name="api_page_feedback",
                ),
                url(
                    r"^poi/?$",
                    poi_feedback.poi_feedback,
                    name="api_poi_feedback",
                ),
                url(
                    r"^event/?$",
                    event_feedback.event_feedback,
                    name="api_event_feedback",
                ),
                url(
                    r"^events/?$",
                    event_list_feedback.event_list_feedback,
                    name="api_event_list_feedback",
                ),
                url(
                    r"^imprint-page/?$",
                    imprint_page_feedback.imprint_page_feedback,
                    name="api_imprint_page_feedbacks",
                ),
                url(
                    r"^map/?$",
                    map_feedback.map_feedback,
                    name="api_map_feedback",
                ),
                url(
                    r"^search/?$",
                    search_result_feedback.search_result_feedback,
                    name="api_search_result_feedback",
                ),
                url(
                    r"^(?:extras|offers)/?$",
                    offer_list_feedback.offer_list_feedback,
                    name="api_offer_list_feedback",
                ),
                url(
                    r"^(?:extra|offer)/?$",
                    offer_feedback.offer_feedback,
                    name="api_offer_feedback",
                ),
            ]
        ),
    ),
]

region_api_urlpatterns = [
    url(r"^$", regions, name="api_regions"),
    url(r"^live/?$", liveregions, name="api_regions_live"),
    url(r"^hidden/?$", hiddenregions, name="api_regions_hidden"),
]


urlpatterns = [
    url(r"^api/regions/", include(region_api_urlpatterns)),
    url(r"^wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
    url(
        r"^api/(?P<region_slug>[-\w]+)/",
        include(
            [
                url(r"^languages/?$", languages, name="api_languages"),
                url(r"^(?:offers|extras)/?$", offers, name="api_offers"),
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
                    name="api_languages",
                ),
                url(
                    r"^(?P<language_slug>[-\w]+)/wp-json/extensions/v3/",
                    include(content_api_urlpatterns),
                ),
            ]
        ),
    ),
]
