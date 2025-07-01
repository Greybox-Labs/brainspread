import json
import logging

logger = logging.getLogger(__name__)


class APIErrorLoggingMiddleware:
    """Middleware to log API errors without modifying responses"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log API endpoints (those containing /api/)
        if "/api/" in request.path and response.status_code >= 400:
            self._log_api_error(request, response)

        return response

    def _log_api_error(self, request, response):
        """Log API error details"""
        try:
            # Try to parse JSON response for error details
            if hasattr(response, "content"):
                try:
                    response_data = json.loads(response.content.decode("utf-8"))
                    error_info = response_data.get("errors", {})
                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_info = "Could not parse response content"
            else:
                error_info = "No response content"

            logger.error(
                f"API Error - {request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"User: {getattr(request, 'user', 'Anonymous')} - "
                f"Errors: {error_info}"
            )
        except Exception as e:
            logger.error(f"Error logging API error: {e}")
