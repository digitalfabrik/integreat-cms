from django.conf.urls import url
from django.db import OperationalError, utils

from . import (
    access_point,
    tests,
    views)
from .utils import activate_federation_feature
from .views import actions

urlpatterns = [
    url(r'^a/$', views.CMSCacheListView.as_view(), name="federation"), #todo: correct url
    url(r'^verify/(?P<cms_id>[-\w]+)/$', actions.verify, name="verify"),
    url(r'^revoke-verification/(?P<cms_id>[0-9,a-f]{20})/$', actions.revoke_verification, name="revoke-verification"),
    url(r'^cms-domains/$', access_point.cms_domains),
    url(r'^cms-data/$', access_point.cms_data),
    url(r'^offer/$', access_point.receive_offer),
    url(r'^test/$', tests.test), #todo: remove test-stuff
    url(r'test-send-offer/$', tests.test_send_offer),
    url(r'test-update/$', tests.test_update),
    url(r'test-ask/$', tests.test_ask)
]

try:
    activate_federation_feature()
except (OperationalError, utils.ProgrammingError):
    pass
