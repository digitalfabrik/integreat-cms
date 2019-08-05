from rest_framework.serializers import ModelSerializer
from cms.models import Extra


class ExtraSerializer(ModelSerializer):
    class Meta:
        model = Extra
        fields = ('name', 'alias', 'thumbnail', 'url', 'post_data', 'region_id', 'template_id')
        depth = 1
