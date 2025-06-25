from typing import TypedDict

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .commands import SendMessageCommand
from .models import ChatSession


class SendMessageResponse(TypedDict):
    response: str


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    message = request.data.get("message", "")
    session_id = request.data.get("session_id")
    api_key = request.data.get("api_key")

    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(uuid=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            session = None

    command = SendMessageCommand(request.user, session, message, api_key)
    result = command.execute()
    return Response({"success": True, "data": result})
