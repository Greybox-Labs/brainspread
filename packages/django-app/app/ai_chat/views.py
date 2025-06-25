import logging
from typing import TypedDict

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .commands import SendMessageCommand
from .commands.send_message import SendMessageCommandError
from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class SendMessageResponse(TypedDict):
    response: str


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Handle AI chat message sending.
    
    Expected request data:
    - message: The user's message (required)
    - session_id: Optional session ID to continue conversation
    
    API key is automatically retrieved from user settings.
    """
    try:
        message = request.data.get("message", "").strip()
        if not message:
            return Response(
                {
                    "success": False, 
                    "error": "Message cannot be empty"
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        session_id = request.data.get("session_id")

        session = None
        if session_id:
            try:
                session = ChatSession.objects.get(uuid=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                logger.warning(f"Session {session_id} not found for user {request.user.id}")
                session = None

        command = SendMessageCommand(request.user, session, message)
        result = command.execute()
        return Response({"success": True, "data": result})

    except SendMessageCommandError as e:
        logger.warning(f"Command error for user {request.user.id}: {str(e)}")
        return Response(
            {
                "success": False,
                "error": str(e),
                "error_type": "configuration_error"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        logger.error(f"Unexpected error in send_message for user {request.user.id}: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "An unexpected error occurred. Please try again.",
                "error_type": "server_error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    Get list of chat sessions for the current user.
    """
    try:
        sessions = ChatSession.objects.filter(user=request.user).order_by('-modified_at')
        
        # Get first message from each session for preview
        sessions_data = []
        for session in sessions:
            first_message = session.messages.filter(role='user').first()
            preview = first_message.content[:100] + "..." if first_message and len(first_message.content) > 100 else (first_message.content if first_message else "")
            
            sessions_data.append({
                "uuid": str(session.uuid),
                "title": session.title or preview or "New Chat",
                "preview": preview,
                "created_at": session.created_at.isoformat(),
                "modified_at": session.modified_at.isoformat(),
                "message_count": session.messages.count()
            })
        
        return Response({"success": True, "data": sessions_data})
        
    except Exception as e:
        logger.error(f"Error fetching chat sessions for user {request.user.id}: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Failed to fetch chat sessions"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_session_detail(request, session_id):
    """
    Get detailed chat session with all messages.
    """
    try:
        session = ChatSession.objects.get(uuid=session_id, user=request.user)
        messages = session.messages.all()
        
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
        
        session_data = {
            "uuid": str(session.uuid),
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "modified_at": session.modified_at.isoformat(),
            "messages": messages_data
        }
        
        return Response({"success": True, "data": session_data})
        
    except ChatSession.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Chat session not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching chat session {session_id} for user {request.user.id}: {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Failed to fetch chat session"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
