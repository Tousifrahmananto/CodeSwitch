from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied


def _csrf_failure_reason(request):
    """Run Django's CSRF validation for a DRF request."""
    check = CSRFCheck(lambda _request: None)
    check.process_request(request)
    return check.process_view(request, None, (), {})


class JWTCookieAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from the 'access_token' httpOnly cookie
    instead of the Authorization header, making tokens invisible to JavaScript
    and immune to XSS-based theft.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None
        user = self.get_user(validated_token)
        reason = _csrf_failure_reason(request)
        if reason:
            raise PermissionDenied(f'CSRF Failed: {reason}')
        return user, validated_token
