"""
Expansion of API-Endpoints for the CMS
"""
from django.conf.urls import include, url

from .v3.feedback import (
    page_feedback,
    search_result_feedback,
    region_feedback,
    offer_feedback,
    offer_list_feedback,
    event_list_feedback,
    event_feedback,
    imprint_page_feedback,
    legacy_feedback_endpoint,
)
from .v3.imprint import imprint
from .v3.languages import languages
from .v3.pages import pages
from .v3.pdf_export import pdf_export
from .v3.push_notifications import sent_push_notifications
from .v3.regions import regions, liveregions, hiddenregions, pushnew
from .v3.offers import offers
from .v3.single_page import single_page

urlpatterns = [
    url(r"^regions/?$", regions),
    url(r"^regions/live/?$", liveregions),
    url(r"^regions/hidden/?$", hiddenregions),
    url(r"^regions/pushnew/?$", pushnew),
    url(
        r"^(?P<region_slug>[-\w]+)/",
        include(
            [
                url(r"^languages/?$", languages),
                url(r"^(?:offers|extras)/?$", offers),
                url(
                    r"^(?P<language_code>[-\w]+)/",
                    include(
                        [
                            url(r"^pages/?$", pages),
                            url(r"^page/?$", single_page),
                            url(r"^pdf/?$", pdf_export),
                            url(
                                r"^sent_push_notifications/?$",
                                sent_push_notifications,
                            ),
                            url(r"^(?:imprint|disclaimer)/?$", imprint),
                            url(r"^(?:offers|extras)/?$", offers),
                            url(
                                r"^feedback/",
                                include(
                                    [
                                        url(
                                            r"^$",
                                            legacy_feedback_endpoint.legacy_feedback_endpoint,
                                        ),
                                        url(
                                            r"^categories/?$",
                                            region_feedback.region_feedback,
                                        ),
                                        url(
                                            r"^page/?$",
                                            page_feedback.page_feedback,
                                        ),
                                        url(
                                            r"^event/?$",
                                            event_feedback.event_feedback,
                                        ),
                                        url(
                                            r"^events/?$",
                                            event_list_feedback.event_list_feedback,
                                        ),
                                        url(
                                            r"^imprint-page/?$",
                                            imprint_page_feedback.imprint_page_feedback,
                                        ),
                                        url(
                                            r"^search/?$",
                                            search_result_feedback.search_result_feedback,
                                        ),
                                        url(
                                            r"^(?:extras|offers)/?$",
                                            offer_list_feedback.offer_list_feedback,
                                        ),
                                        url(
                                            r"^(?:extra|offer)/?$",
                                            offer_feedback.offer_feedback,
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
