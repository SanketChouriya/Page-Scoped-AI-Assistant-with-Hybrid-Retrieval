from rest_framework import serializers

class PageSectionSerializer(serializers.Serializer):
    type = serializers.CharField()
    text = serializers.CharField(max_length=50000)

class IngestPageSerializer(serializers.Serializer):
    url = serializers.URLField()
    sections = PageSectionSerializer(many=True)