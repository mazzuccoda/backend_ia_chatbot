import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_api.permissions import HasApiKey, HasScope

from .models import ConversationMemory
from .serializers import MemoryGetSerializer, MemorySaveSerializer

logger = logging.getLogger(__name__)


class MemorySaveView(APIView):
    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def post(self, request):
        serializer = MemorySaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        obj, created = ConversationMemory.objects.update_or_create(
            user_id=d["user_id"],
            conversation_id=d["conversation_id"],
            key=d["key"],
            defaults={"value": d["value"]},
        )
        return Response(
            {
                "status": "ok",
                "data": {
                    "user_id": obj.user_id,
                    "conversation_id": obj.conversation_id,
                    "key": obj.key,
                    "created": created,
                },
            },
            status=status.HTTP_200_OK,
        )


class MemoryGetView(APIView):
    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def post(self, request):
        serializer = MemoryGetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        qs = ConversationMemory.objects.filter(
            user_id=d["user_id"],
            conversation_id=d["conversation_id"],
        )
        if "key" in d:
            qs = qs.filter(key=d["key"])

        memories = {m.key: m.value for m in qs}
        return Response(
            {"status": "ok", "data": memories},
            status=status.HTTP_200_OK,
        )
