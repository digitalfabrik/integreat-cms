from rest_framework.generics import ListAPIView
from api.v3.serializers import LocationSerializer

from cms.models import POI


class LocationView(ListAPIView):
    """
    This API should return a list of locations for a site
    """
    serializer_class = LocationSerializer

    def get_queryset(self):
        site = self.kwargs['site']
        return POI.objects.filter(site=site)
