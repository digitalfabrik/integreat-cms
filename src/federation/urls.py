from django.conf.urls import url

from . import (
    access_point,
    tests,
    views)
from .views import actions

urlpatterns = [
    url(r'^a/$', views.CMSCacheListView.as_view(), name="federation"), #todo: correct url
    url(r'^activate/(?P<cms_id>\d+)/$', actions.activate, name="activate"),
    url(r'^deactivate/(?P<cms_id>\d+)/$', actions.deactivate, name="deactivate"),
    url(r'^check-availability/(?P<cms_id>\d+)/$', actions.check_availability, name="check_availability"),
    url(r'^cms-domains/$', access_point.cms_domains),
    url(r'^cms-name/$', access_point.cms_name),
    url(r'^offer/$', access_point.receive_offer),
    url(r'^test/$', tests.test), #todo: remove test-stuff
    url(r'test-send-offer/$', tests.test_send_offer),
    url(r'test-update/$', tests.test_update),
    url(r'test-ask/$', tests.test_ask)
]
