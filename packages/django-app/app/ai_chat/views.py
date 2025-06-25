import logging
from typing import TypedDict

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .commands import SendMessageCommand
from .commands.send_message import SendMessageCommandError
from .models import (
    AIProvider,
    ChatSession,
    UserAISettings,
    UserProviderConfig,
)
from .services.ai_service_factory import AIServiceFactory
from .services.user_settings_service import UserSettingsService

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
                {"success": False, "error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_id = request.data.get("session_id")

        session = None
        if session_id:
            try:
                session = ChatSession.objects.get(uuid=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                logger.warning(
                    f"Session {session_id} not found for user {request.user.id}"
                )
                session = None

        command = SendMessageCommand(request.user, session, message)
        result = command.execute()
        return Response({"success": True, "data": result})

    except SendMessageCommandError as e:
        logger.warning(f"Command error for user {request.user.id}: {str(e)}")
        return Response(
            {"success": False, "error": str(e), "error_type": "configuration_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.error(
            f"Unexpected error in send_message for user {request.user.id}: {str(e)}"
        )
        return Response(
            {
                "success": False,
                "error": "An unexpected error occurred. Please try again.",
                "error_type": "server_error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    Get list of chat sessions for the current user.
    """
    try:
        sessions = ChatSession.objects.filter(user=request.user).order_by(
            "-modified_at"
        )

        # Get first message from each session for preview
        sessions_data = []
        for session in sessions:
            first_message = session.messages.filter(role="user").first()
            preview = (
                first_message.content[:100] + "..."
                if first_message and len(first_message.content) > 100
                else (first_message.content if first_message else "")
            )

            sessions_data.append(
                {
                    "uuid": str(session.uuid),
                    "title": session.title or preview or "New Chat",
                    "preview": preview,
                    "created_at": session.created_at.isoformat(),
                    "modified_at": session.modified_at.isoformat(),
                    "message_count": session.messages.count(),
                }
            )

        return Response({"success": True, "data": sessions_data})

    except Exception as e:
        logger.error(
            f"Error fetching chat sessions for user {request.user.id}: {str(e)}"
        )
        return Response(
            {"success": False, "error": "Failed to fetch chat sessions"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

        session_data = {
            "uuid": str(session.uuid),
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "modified_at": session.modified_at.isoformat(),
            "messages": messages_data,
        }

        return Response({"success": True, "data": session_data})

    except ChatSession.DoesNotExist:
        return Response(
            {"success": False, "error": "Chat session not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            f"Error fetching chat session {session_id} for user {request.user.id}: {str(e)}"
        )
        return Response(
            {"success": False, "error": "Failed to fetch chat session"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_settings(request):
    """
    Get AI settings for the current user.
    """
    try:
        # Get available providers
        providers = AIProvider.objects.all()
        providers_data = [
            {
                "id": provider.id,
                "uuid": str(provider.uuid),
                "name": provider.name,
                "models": AIServiceFactory.get_available_models(provider.name),
            }
            for provider in providers
        ]

        # Get user's current settings
        user_settings = UserSettingsService.get_user_settings(request.user)
        current_provider = None
        current_model = None

        if user_settings:
            current_provider = (
                user_settings.provider.name if user_settings.provider else None
            )
            current_model = user_settings.default_model

        # Get user provider configurations
        provider_configs = UserProviderConfig.objects.filter(user=request.user)
        configs_data = {}

        for config in provider_configs:
            configs_data[config.provider.name] = {
                "is_enabled": config.is_enabled,
                "has_api_key": bool(config.api_key),
                "enabled_models": config.enabled_models,
            }

        response_data = {
            "providers": providers_data,
            "current_provider": current_provider,
            "current_model": current_model,
            "provider_configs": configs_data,
        }

        return Response({"success": True, "data": response_data})

    except Exception as e:
        logger.error(f"Error fetching AI settings for user {request.user.id}: {str(e)}")
        return Response(
            {"success": False, "error": "Failed to fetch AI settings"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_ai_settings(request):
    """
    Update AI settings for the current user.
    """
    try:
        provider_name = request.data.get("provider")
        model = request.data.get("model")
        api_keys = request.data.get("api_keys", {})  # Dict of provider_name: api_key
        provider_configs = request.data.get(
            "provider_configs", {}
        )  # Dict of provider configs

        # Update user AI settings
        if provider_name and model:
            try:
                provider = AIProvider.objects.get(name__iexact=provider_name)
            except AIProvider.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "error": f"Provider '{provider_name}' not found",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get or create user settings
            user_settings, created = UserAISettings.objects.get_or_create(
                user=request.user,
                defaults={"provider": provider, "default_model": model},
            )

            if not created:
                user_settings.provider = provider
                user_settings.default_model = model
                user_settings.save()

        # Update provider configurations
        for provider_name, config_data in provider_configs.items():
            try:
                provider = AIProvider.objects.get(name__iexact=provider_name)
                provider_config, created = UserProviderConfig.objects.get_or_create(
                    user=request.user,
                    provider=provider,
                    defaults={
                        "is_enabled": config_data.get("is_enabled", True),
                        "enabled_models": config_data.get("enabled_models", []),
                    },
                )

                if not created:
                    provider_config.is_enabled = config_data.get(
                        "is_enabled", provider_config.is_enabled
                    )
                    provider_config.enabled_models = config_data.get(
                        "enabled_models", provider_config.enabled_models
                    )
                    provider_config.save()

            except AIProvider.DoesNotExist:
                logger.warning(
                    f"Provider '{provider_name}' not found when updating config"
                )
                continue

        # Update API keys
        for provider_name, api_key in api_keys.items():
            try:
                provider = AIProvider.objects.get(name__iexact=provider_name)
                provider_config, created = UserProviderConfig.objects.get_or_create(
                    user=request.user, provider=provider, defaults={"api_key": api_key}
                )

                if not created:
                    provider_config.api_key = api_key
                    provider_config.save()

            except AIProvider.DoesNotExist:
                logger.warning(
                    f"Provider '{provider_name}' not found when updating API key"
                )
                continue

        return Response(
            {"success": True, "data": {"message": "AI settings updated successfully"}}
        )

    except Exception as e:
        logger.error(f"Error updating AI settings for user {request.user.id}: {str(e)}")
        return Response(
            {"success": False, "error": "Failed to update AI settings"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
