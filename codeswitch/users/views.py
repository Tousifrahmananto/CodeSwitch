from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
from .serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


def _set_auth_cookies(response, refresh):
    """Attach access + refresh tokens as httpOnly cookies.

    In production the frontend (Vercel) and backend (Railway) are on different
    origins, so cookies must use SameSite=None; Secure to be sent cross-site.
    In local development (DEBUG=True) SameSite=Lax is fine since both services
    run on localhost.
    """
    secure = not settings.DEBUG
    # Cross-origin production: SameSite=None (must pair with Secure=True)
    # Same-origin local dev:   SameSite=Lax  (works on localhost without HTTPS)
    samesite = 'None' if not settings.DEBUG else 'Lax'
    response.set_cookie(
        'access_token',
        str(refresh.access_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=3600,          # 1 hour — matches SIMPLE_JWT ACCESS_TOKEN_LIFETIME
    )
    response.set_cookie(
        'refresh_token',
        str(refresh),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=604800,        # 7 days — matches SIMPLE_JWT REFRESH_TOKEN_LIFETIME
    )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        identifier = (request.data.get('username') or '').strip()
        password = request.data.get('password')

        user = None
        if '@' in identifier:
            # Email login — resolve to username first
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        else:
            user = authenticate(username=identifier, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            response = Response({'user': UserProfileSerializer(user).data})
            _set_auth_cookies(response, refresh)
            return response

        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # Already expired / blacklisted — still clear cookies

        response = Response({'message': 'Logged out successfully.'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class CookieTokenRefreshView(APIView):
    """
    POST /api/token/refresh/
    Reads the refresh token from the httpOnly cookie, issues a new access token
    (and rotated refresh token), and sets both back as cookies.
    No request body required.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'No refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
            response = Response({'detail': 'Token refreshed.'})
            _set_auth_cookies(response, refresh)
            return response
        except TokenError:
            response = Response({'error': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response


class MeView(APIView):
    """
    GET /api/me/
    Returns the current authenticated user's profile.
    Used on app load to validate the session cookie.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PublicProfileView(APIView):
    """GET /api/profile/<username>/ — Public stats for any user (no auth required)."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        from converter.models import ConversionHistory
        from learning.models import UserProgress, LearningModule

        conversion_count = ConversionHistory.objects.filter(user=user).count()
        completed_progress = UserProgress.objects.filter(user=user, completed=True)
        lessons_completed = completed_progress.count()
        languages_used = list(
            ConversionHistory.objects.filter(user=user)
            .values_list('source_language', flat=True)
            .distinct()
        )

        # Count modules where all lessons are completed by this user
        modules_completed = 0
        for module in LearningModule.objects.all():
            total = module.lessons.count()
            if total == 0:
                continue
            done = completed_progress.filter(module=module).count()
            if done >= total:
                modules_completed += 1

        return Response({
            'username': user.username,
            'date_joined': user.date_joined,
            'conversion_count': conversion_count,
            'lessons_completed': lessons_completed,
            'modules_completed': modules_completed,
            'languages_used': languages_used,
        })
