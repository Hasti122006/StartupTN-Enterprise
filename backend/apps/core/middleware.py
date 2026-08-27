import logging

SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie", "set-cookie"}
SENSITIVE_BODY_FIELDS = {"password", "login_password", "username", "email", "login_email"}

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Request bodies can contain passwords and headers can contain the n8n key.
        # Log only request metadata; endpoint-specific code logs safe context.
        logger.info("%s %s", request.method, request.path)
        response = self.get_response(request)
        logger.info("%s %s -> %s", request.method, request.path, response.status_code)
        return response
