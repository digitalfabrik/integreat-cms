from cms.models import Extra
from rest_framework.serializers import ModelSerializer

class ExtraSerializer(ModelSerializer):
    class Meta:
        model = Extra
        fields = ('name', 'alias', 'thumbnail', 'url', 'post_data', 'site_id', 'template_id')
        depth = 1
