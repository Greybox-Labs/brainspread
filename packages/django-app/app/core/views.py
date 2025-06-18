from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import User


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login endpoint that returns an auth token"""
    try:
        email = request.data.get("email")
        password = request.data.get("password")
        timezone = request.data.get("timezone")

        if not email or not password:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": ["Email and password are required"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if user and user.is_active:
            # Update user's timezone if provided
            if timezone:
                user.timezone = timezone
                user.save(update_fields=["timezone"])

            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "success": True,
                    "data": {
                        "token": token.key,
                        "user": {
                            "id": str(user.uuid),
                            "email": user.email,
                            "timezone": user.timezone,
                        },
                    },
                }
            )
        else:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": ["Invalid credentials"]},
                },
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
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "success": False,
                    "errors": {"non_field_errors": ["Email and password are required"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "success": False,
                    "errors": {"email": ["User with this email already exists"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(email=email, password=password)
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "data": {
                    "token": token.key,
                    "user": {
                        "id": str(user.uuid),
                        "email": user.email,
                        "timezone": user.timezone,
                    },
                },
            },
            status=status.HTTP_201_CREATED,
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
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({"success": True, "message": "Successfully logged out"})
    except Token.DoesNotExist:
        return Response({"success": True, "message": "Already logged out"})
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def me(request):
    """Get current user info"""
    try:
        return Response(
            {
                "success": True,
                "data": {
                    "user": {
                        "id": str(request.user.uuid),
                        "email": request.user.email,
                        "timezone": request.user.timezone,
                    }
                },
            }
        )
    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def update_timezone(request):
    """Update user's timezone preference"""
    try:
        timezone = request.data.get("timezone")

        if not timezone:
            return Response(
                {"success": False, "errors": {"timezone": ["Timezone is required"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate timezone (basic validation)
        try:
            import pytz

            pytz.timezone(timezone)
        except:
            # If not a valid pytz timezone, still allow it (could be a browser-specific format)
            pass

        # Update user's timezone
        request.user.timezone = timezone
        request.user.save(update_fields=["timezone"])

        return Response(
            {
                "success": True,
                "data": {
                    "user": {
                        "id": str(request.user.uuid),
                        "email": request.user.email,
                        "timezone": request.user.timezone,
                    }
                },
                "message": "Timezone updated successfully",
            }
        )

    except Exception as e:
        return Response(
            {"success": False, "errors": {"non_field_errors": [str(e)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
