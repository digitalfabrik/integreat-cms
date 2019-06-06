from cms.models import Extra
from rest_framework.generics import ListAPIView

from api.v3.serializers import ExtraSerializer


class Extras(ListAPIView):

    """
    This view should return a list of extras for a site
    """
    serializer_class = ExtraSerializer

    def get_queryset(self):
        site = self.kwargs['site']
        return Extra.objects.filter(site=site)
