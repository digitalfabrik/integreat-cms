from rest_framework import generics, serializers

from ..utils import ReadOnlyModelSerializer


class LanguageSerializer(ReadOnlyModelSerializer):
    id = serializers.IntegerField()
    code = serializers.SlugField(source="slug")
    bcp47_tag = serializers.SlugField()
    native_name = serializers.CharField()
    dir = serializers.CharField(source="text_direction")


class LanguageView(generics.ListAPIView):
    serializer_class = LanguageSerializer

    def get_queryset(self):
        return self.request.region.visible_languages
