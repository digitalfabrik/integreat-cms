"""
Expansion of API-Endpoints for the CMS
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import include, path, re_path

from ..core import settings
from .v3.chat import user_chat
from .v3.events import events
from .v3.feedback import (
    event_feedback,
    event_list_feedback,
    imprint_page_feedback,
    legacy_feedback_endpoint,
    map_feedback,
    offer_feedback,
    offer_list_feedback,
    page_feedback,
    poi_feedback,
    region_feedback,
    search_result_feedback,
)
from .v3.imprint import imprint
from .v3.languages import languages
from .v3.location_categories import location_categories
from .v3.locations import locations
from .v3.offers import offers
from .v3.pages import (
    children,
    pages,
    parents,
    push_page_translation_content,
    single_page,
)
from .v3.pdf_export import pdf_export
from .v3.push_notifications import sent_push_notifications
from .v3.regions import region_by_slug, regions
from .v3.social_media_headers import (
    event_social_media_headers,
    location_social_media_headers,
    news_social_media_headers,
    page_social_media_headers,
    region_social_media_headers,
    root_social_media_headers,
)

if TYPE_CHECKING:
    from typing import Final

    from django.urls.resolvers import URLPattern

#: The namespace for this URL config (see :attr:`django.urls.ResolverMatch.app_name`)
app_name: Final = "api"

content_api_urlpatterns: list[URLPattern] = [
    path("pages/", pages, name="pages"),
    path("locations/", locations, name="locations"),
    path("location-categories/", location_categories, name="location_categories"),
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
    path("chat/<slug:device_id>/", user_chat.chat, name="chat"),
    path("chat/<slug:device_id>/<slug:attachment_id>/", user_chat.chat, name="chat"),
]

region_api_urlpatterns: list[URLPattern] = [
    path("", regions, name="regions"),
    path("<slug:region_slug>/", region_by_slug, name="region_by_slug"),
]

social_media_api_urlpatterns = [
    path("", root_social_media_headers, name="social_root"),
    *(
        path(
            f"{reserved}/",
            include(
                [
                    path(
                        "",
                        root_social_media_headers,
                        name=f"social_root_reserved_{reserved}",
                    ),
                    path(
                        "<slug:language_slug>/",
                        root_social_media_headers,
                        name=f"social_root_reserved_default_language_{reserved}",
                    ),
                ]
            ),
        )
        for reserved in settings.RESERVED_REGION_SLUGS
    ),
    path(
        "<slug:region_slug>/",
        region_social_media_headers,
        name="social_region_default_language",
    ),
    path(
        "<slug:region_slug>/<slug:language_slug>/",
        include(
            [
                path("", region_social_media_headers, name="social_region"),
                path(
                    "news/local/",
                    region_social_media_headers,
                    name="social_region_reserved_local_news",
                ),
                re_path(
                    r"^news/tunews/[\w-]+/$",
                    region_social_media_headers,
                    name="social_region_reserved_tunews",
                ),
                *(
                    path(
                        f"{reserved}/",
                        region_social_media_headers,
                        name=f"social_region_reserved_{reserved}",
                    )
                    for reserved in settings.RESERVED_REGION_PAGE_PATTERNS
                ),
                path(
                    "events/<slug:slug>/",
                    event_social_media_headers,
                    name="social_region_event_page",
                ),
                path(
                    "news/local/<slug:slug>/",
                    news_social_media_headers,
                    name="social_region_local_news_page",
                ),
                path(
                    "locations/<slug:slug>/",
                    location_social_media_headers,
                    name="social_region_location_page",
                ),
                path(
                    "<path:path>/",
                    page_social_media_headers,
                    name="social_region_content",
                ),
            ]
        ),
    ),
]

#: The url patterns of this module (see :doc:`django:topics/http/urls`)
urlpatterns: list[URLPattern] = [
    path("api/v3/regions/", include(region_api_urlpatterns)),
    path("wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
    path("api/v3/social/", include(social_media_api_urlpatterns)),
    path(
        "api/v3/<slug:region_slug>/",
        include(
            [
                path("languages/", languages, name="languages"),
                path("offers/", offers, name="offers"),
                path("extras/", offers, name="offers"),
                path(
                    "<slug:device_id>/is_chat_enabled/",
                    user_chat.is_chat_enabled_for_user,
                    name="is_chat_enabled_for_user",
                ),
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
