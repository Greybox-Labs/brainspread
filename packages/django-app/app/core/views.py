from typing import TypedDict

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.commands import (
    GetUserProfileCommand,
    LoginCommand,
    LogoutCommand,
    RegisterCommand,
    UpdateThemeCommand,
    UpdateTimezoneCommand,
)
from core.forms import LoginForm, RegisterForm, UpdateThemeForm, UpdateTimezoneForm
from core.models.user import UserData


# API Response Types for this view
class LoginResponse(TypedDict):
    token: str
    user: UserData


class RegisterResponse(TypedDict):
    token: str
    user: UserData


class UpdateThemeResponse(TypedDict):
    user: UserData


class UpdateTimezoneResponse(TypedDict):
    user: UserData


class GetUserProfileResponse(TypedDict):
    user: UserData


class LogoutResponse(TypedDict):
    message: str


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login endpoint that returns an auth token"""
    try:
        form = LoginForm(request.data)
        if form.is_valid():
            command = LoginCommand(form)
            result = command.execute()
            data: LoginResponse = {
                "token": result.token,
                "user": result.user.to_user_data(),
            }
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
            result = command.execute()
            data: RegisterResponse = {
                "token": result.token,
                "user": result.user.to_user_data(),
            }
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
        message = command.execute()
        data: LogoutResponse = {"message": message}
        return Response({"success": True, "data": data})
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
        user = command.execute()
        data: GetUserProfileResponse = {"user": user.to_user_data()}
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
            updated_user = command.execute()
            data: UpdateTimezoneResponse = {"user": updated_user.to_user_data()}
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


@api_view(["POST"])
def update_theme(request):
    """Update user's theme preference"""
    try:
        form = UpdateThemeForm(request.data)
        if form.is_valid():
            command = UpdateThemeCommand(form, request.user)
            updated_user = command.execute()
            data: UpdateThemeResponse = {"user": updated_user.to_user_data()}
            return Response(
                {
                    "success": True,
                    "data": data,
                    "message": "Theme updated successfully",
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
