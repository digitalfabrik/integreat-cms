from rest_framework import generics, serializers
from rest_framework.schemas.openapi import AutoSchema

from ...cms.constants import region_status
from ...cms.models import Region
from ..utils import ReadOnlyModelSerializer


class RegionSerializer(ReadOnlyModelSerializer):
    """
    This class serializes the ``integreat_cms.cms.models.regions.region.Region`` model
    """

    id = serializers.IntegerField()
    name = serializers.CharField(source="full_name")
    path = serializers.SlugField(source="slug")
    live = serializers.BooleanField(source="is_live")
    prefix = serializers.CharField()
    name_without_prefix = serializers.CharField(source="name")
    plz = serializers.CharField(source="postal_code")
    extras = serializers.BooleanField(source="offers.exists")
    events = serializers.BooleanField(source="events_enabled")
    pois = serializers.BooleanField(source="locations_enabled")
    push_notifications = serializers.BooleanField(source="push_notifications_enabled")
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    bounding_box = serializers.JSONField(source="bounding_box.api_representation")
    aliases = serializers.JSONField()
    tunews = serializers.BooleanField(source="tunews_enabled")


class FilteredRegionSerializer(RegionSerializer):
    """
    A region serializer that does not include the `live` field
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.pop("live")


class RegionListView(generics.ListAPIView):
    """
    This endpoint returns all non-archived regions
    """

    queryset = Region.objects.exclude(status=region_status.ARCHIVED)
    serializer_class = RegionSerializer


class LiveRegionListView(generics.ListAPIView):
    """
    This endpoint returns all live regions
    """

    schema = AutoSchema(operation_id_base="LiveRegions")
    queryset = Region.objects.filter(status=region_status.ACTIVE)
    serializer_class = FilteredRegionSerializer


class HiddenRegionListView(generics.ListAPIView):
    """
    This endpoint returns all hidden regions
    """

    schema = AutoSchema(operation_id_base="HiddenRegions")
    queryset = Region.objects.filter(status=region_status.HIDDEN)
    serializer_class = FilteredRegionSerializer
