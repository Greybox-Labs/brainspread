from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

# For now, use a simple approach - in production you'd want proper auth
def get_current_user():
    """Get the current user for MCP operations"""
    # This could be enhanced to support multiple users via session/token
    try:
        return User.objects.get(email="admin@email.com")  # Default admin user
    except ObjectDoesNotExist:
        raise Exception("Default user not found. Please create admin user first.")

# Future enhancement: support user switching
def set_current_user(user_id: str):
    """Switch to different user context"""
    pass