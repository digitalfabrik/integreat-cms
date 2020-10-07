"""
Expansion of API-Endpoints for the CMS
"""
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt

from .v3.feedback import (
    page_feedback,
    search_result_feedback,
    region_feedback,
    offer_list_feedback,
    event_list_feedback,
)
from .v3.languages import languages
from .v3.pages import pages
from .v3.push_notifications import sent_push_notifications
from .v3.regions import regions, liveregions, hiddenregions, pushnew
from .v3.offers import offers
from .v3.single_page import single_page

urlpatterns = [
    url(r"regions/$", regions),
    url(r"regions/live/$", liveregions),
    url(r"regions/hidden/$", hiddenregions),
    url(r"regions/pushnew/$", pushnew),
    url(
        r"(?P<region_slug>[-\w]+)/",
        include(
            [
                url(r"languages/$", languages),
                url(r"offers/$", offers),
                url(
                    r"(?P<language_code>[-\w]+)/sent_push_notifications/$",
                    sent_push_notifications,
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/$",
                    page_feedback.page_feedback,  # todo: add legacy endpoint
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/page$",
                    page_feedback.page_feedback,
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/categories$",
                    region_feedback.region_feedback,
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/search$",
                    search_result_feedback.search_result_feedback,
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/extras$",
                    offer_list_feedback.offer_list_feedback,
                ),
                url(
                    r"(?P<language_code>[-\w]+)/feedback/events$",
                    event_list_feedback.event_list_feedback,
                ),
                url(r"(?P<language_code>[-\w]+)/pages/$", pages),
                url(r"(?P<language_code>[-\w]+)/offers/$", offers),
                url(r"(?P<language_code>[-\w]+)/page/$", single_page),
            ]
        ),
    ),
]
