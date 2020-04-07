from django.conf.urls import url
from django.db import OperationalError

from . import (
    access_point,
    tests
)
from .utils import activate_federation_feature

urlpatterns = [
    url(r'^cms-domains/', access_point.cms_domains),
    url(r'^cms-data/', access_point.cms_data),
    url(r'^offer/', access_point.receive_offer),
    url(r'^test/', tests.test), #todo: remove test-stuff
    url(r'test-send-offer', tests.test_send_offer),
    url(r'test-update', tests.test_update),
    url(r'test-ask', tests.test_ask)
]

try:
    activate_federation_feature()
except OperationalError:
    pass
