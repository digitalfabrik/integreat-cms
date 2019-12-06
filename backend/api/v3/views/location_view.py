from rest_framework.generics import ListAPIView

from api.v3.serializers import LocationSerializer
from cms.models import POI


class LocationView(ListAPIView):
    """
    This API should return a list of locations for a region
    """
    serializer_class = LocationSerializer

    def get_queryset(self):
        region = self.kwargs['region']
        return POI.objects.filter(region=region)
