from rest_framework import serializers


class ReadOnlyModelSerializer(serializers.Serializer):
    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        for field in fields:
            fields[field].read_only = True
        return fields
