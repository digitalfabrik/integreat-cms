from django.urls import include, path
from rest_framework import routers

from . import v3

content_api_urlpatterns = [
    path("pages/", v3.PageView.as_view(), name="pages"),
    # path("locations/", v3.LocationView.as_view(), name="locations"),
]

region_api_urlpatterns = [
    path("", v3.RegionListView.as_view(), name="regions"),
    path("live", v3.LiveRegionListView.as_view(), name="regions_live"),
    path("hidden", v3.HiddenRegionListView.as_view(), name="regions_hidden"),
]

# Wire up our API using automatic URL routing.
urlpatterns = [
    path("apiv2/regions/", include(region_api_urlpatterns)),
    path("wp-json/extensions/v3/sites/", include(region_api_urlpatterns)),
    path(
        "apiv2/<slug:region_slug>/",
        include(
            [
                path("languages/", v3.LanguageView.as_view(), name="languages"),
                path("offers/", v3.OfferView.as_view(), name="offers"),
                path("extras/", v3.OfferView.as_view(), name="offers"),
                path("<slug:language_slug>/", include(content_api_urlpatterns)),
            ]
        ),
    ),
]
