from rest_framework.serializers import ModelSerializer

from cms.models import POI


class LocationSerializer(ModelSerializer):
    class Meta:
        model = POI
        fields = ('id', 'address', 'postcode', 'city', 'region', 'country', 'latitude', 'longitude')
        depth = 1
