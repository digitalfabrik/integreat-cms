from django.urls import include, path
from rest_framework import routers

from . import v3

region_api_urlpatterns = [
    path("", v3.RegionListView.as_view(), name="regions"),
    path("live", v3.LiveRegionListView.as_view(), name="regions_live"),
    path("hidden", v3.HiddenRegionListView.as_view(), name="regions_hidden"),
]


# Wire up our API using automatic URL routing.
urlpatterns = [
    path("apiv2/regions/", include(region_api_urlpatterns)),
    path("wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
]
