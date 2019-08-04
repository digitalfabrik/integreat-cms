from django.shortcuts import get_object_or_404

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from api.v3.serializers import ExtraSerializer

from cms.models import Extra


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

    def retrieve_extra(self, request, extra_id=None):
        extra = get_object_or_404(self.get_queryset(), id=extra_id)
        serializer = ExtraSerializer(extra)
        return Response(serializer.data)
