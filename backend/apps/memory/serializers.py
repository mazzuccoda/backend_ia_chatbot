from rest_framework import serializers


class MemorySaveSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    conversation_id = serializers.CharField(max_length=100)
    key = serializers.CharField(max_length=100)
    value = serializers.JSONField()


class MemoryGetSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    conversation_id = serializers.CharField(max_length=100)
    key = serializers.CharField(max_length=100, required=False)
