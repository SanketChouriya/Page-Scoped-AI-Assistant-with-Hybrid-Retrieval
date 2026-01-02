from rest_framework import serializers


class AskSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    question = serializers.CharField(max_length=20000)
