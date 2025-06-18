from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .forms import LoginForm, RegisterForm, UpdateTimezoneForm
from .commands.login_command import LoginCommand
from .commands.register_command import RegisterCommand
from .commands.logout_command import LogoutCommand
from .commands.update_timezone_command import UpdateTimezoneCommand
from .commands.get_user_profile_command import GetUserProfileCommand


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login endpoint that returns an auth token"""
    try:
        form = LoginForm(request.data)
        if form.is_valid():
            command = LoginCommand(form)
            data = command.execute()
            return Response({"success": True, "data": data})
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Register endpoint that creates a new user and returns an auth token"""
    try:
        form = RegisterForm(request.data)
        if form.is_valid():
            command = RegisterCommand(form)
            data = command.execute()
            return Response(
                {"success": True, "data": data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def logout(request):
    """Logout endpoint that deletes the auth token"""
    try:
        command = LogoutCommand(request.user)
        data = command.execute()
        return Response({"success": True, **data})
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def me(request):
    """Get current user info"""
    try:
        command = GetUserProfileCommand(request.user)
        data = command.execute()
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def update_timezone(request):
    """Update user's timezone preference"""
    try:
        form = UpdateTimezoneForm(request.data)
        if form.is_valid():
            command = UpdateTimezoneCommand(form, request.user)
            data = command.execute()
            return Response(
                {
                    "success": True,
                    "data": data,
                    "message": "Timezone updated successfully",
                }
            )
        else:
            return Response(
                {"success": False, "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ValidationError as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
