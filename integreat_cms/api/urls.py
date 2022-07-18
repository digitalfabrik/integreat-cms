"""
Expansion of API-Endpoints for the CMS
"""
from django.urls import include, path, re_path

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
from .v3.pages import (
    pages,
    children,
    parents,
    single_page,
    push_page_translation_content,
)
from .v3.pdf_export import pdf_export
from .v3.push_notifications import sent_push_notifications
from .v3.regions import regions, liveregions, hiddenregions
from .v3.offers import offers


#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name = "api"

content_api_urlpatterns = [
    path("pages/", pages, name="pages"),
    path("locations/", locations, name="locations"),
    path("events/", events, name="events"),
    path("page/", single_page, name="single_page"),
    path("post/", single_page, name="single_page"),
    path("children/", children, name="children"),
    path("parents/", parents, name="parents"),
    path("pdf/", pdf_export, name="pdf_export"),
    path(
        "fcm/",
        sent_push_notifications,
        name="sent_push_notifications",
    ),
    path("imprint/", imprint, name="imprint"),
    path("disclaimer/", imprint, name="imprint"),
    path("offers/", offers, name="offers"),
    path("extras/", offers, name="offers"),
    path(
        "pushpage/", push_page_translation_content, name="push_page_translation_content"
    ),
    re_path(
        r"^feedback/?$",
        legacy_feedback_endpoint.legacy_feedback_endpoint,
        name="legacy_feedback_endpoint",
    ),
    path(
        "feedback/",
        include(
            [
                re_path(
                    r"^categories/?$",
                    region_feedback.region_feedback,
                    name="region_feedback",
                ),
                re_path(r"^page/?$", page_feedback.page_feedback, name="page_feedback"),
                re_path(r"^poi/?$", poi_feedback.poi_feedback, name="poi_feedback"),
                re_path(
                    r"^event/?$", event_feedback.event_feedback, name="event_feedback"
                ),
                re_path(
                    r"^events/?$",
                    event_list_feedback.event_list_feedback,
                    name="event_list_feedback",
                ),
                re_path(
                    r"^imprint-page/?$",
                    imprint_page_feedback.imprint_page_feedback,
                    name="imprint_page_feedbacks",
                ),
                re_path(r"^map/?$", map_feedback.map_feedback, name="map_feedback"),
                re_path(
                    r"^search/?$",
                    search_result_feedback.search_result_feedback,
                    name="search_result_feedback",
                ),
                re_path(
                    r"^offers/?$",
                    offer_list_feedback.offer_list_feedback,
                    name="offer_list_feedback",
                ),
                re_path(
                    r"^extras/?$",
                    offer_list_feedback.offer_list_feedback,
                    name="offer_list_feedback",
                ),
                re_path(
                    r"^offer/?$", offer_feedback.offer_feedback, name="offer_feedback"
                ),
                re_path(
                    r"^extra/?$", offer_feedback.offer_feedback, name="offer_feedback"
                ),
            ]
        ),
    ),
]

region_api_urlpatterns = [
    path("", regions, name="regions"),
    path("live/", liveregions, name="regions_live"),
    path("hidden/", hiddenregions, name="regions_hidden"),
]

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns = [
    path("api/regions/", include(region_api_urlpatterns)),
    path("wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
    path(
        "api/<slug:region_slug>/",
        include(
            [
                path("languages/", languages, name="languages"),
                path("offers/", offers, name="offers"),
                path("extras/", offers, name="offers"),
                path("<slug:language_slug>/", include(content_api_urlpatterns)),
            ]
        ),
    ),
    path(
        "<slug:region_slug>/",
        include(
            [
                path(
                    "de/wp-json/extensions/v3/languages/", languages, name="languages"
                ),
                path(
                    "<slug:language_slug>/wp-json/extensions/v3/",
                    include(content_api_urlpatterns),
                ),
                path(
                    "<slug:language_slug>/wp-json/ig-mpdf/v1/pdf/",
                    pdf_export,
                    name="pdf_export",
                ),
            ]
        ),
    ),
]
