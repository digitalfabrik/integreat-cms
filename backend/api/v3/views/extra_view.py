from django.shortcuts import get_object_or_404

from cms.models import Extra
from rest_framework.generics import ListAPIView, RetrieveAPIView
from api.v3.serializers import ExtraSerializer
from rest_framework.response import Response


class ExtrasView(ListAPIView):
    """
    This API should return a list of extras for a site
    """
    serializer_class = ExtraSerializer

    def get_queryset(self):
        site = self.kwargs['site']
        return Extra.objects.filter(site=site)


class ExtraView(RetrieveAPIView):
    """
    This API should return a specific extra detail from ID
    """
    serializer_class = ExtraSerializer
    queryset = Extra.objects.all()

    def retrieve(self, request, id=None):
        extra = get_object_or_404(self.get_queryset(), id=id)
        serializer = ExtraSerializer(extra)
        return Response(serializer.data)

