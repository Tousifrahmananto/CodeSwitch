from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.text import slugify
from .serializers import RegisterSerializer, UserProfileSerializer
from converter.throttles import (
    CsrfTokenThrottle, LoginThrottle, ProfileWriteThrottle,
    PublicProfileThrottle, RegisterThrottle, TokenRefreshThrottle,
    TrackedUserThrottle,
)
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

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


@method_decorator(csrf_protect, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        from django.contrib.auth import authenticate

        identifier = (request.data.get('username') or '').strip()
        password = request.data.get('password')

        user = None
        if '@' in identifier:
            # Email login — resolve to username first
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        else:
            user = authenticate(request, username=identifier, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            response = Response({'user': UserProfileSerializer(user, context={'request': request}).data})
            _set_auth_cookies(response, refresh)
            return response

        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


def _unique_google_username(email):
    """Generate a stable, human-ish username from a verified Google email."""
    prefix = (email.split('@', 1)[0] or 'google-user').strip()
    base = slugify(prefix).replace('-', '_')[:140] or 'google_user'
    username = base
    counter = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix = f'_{counter}'
        username = f'{base[:150 - len(suffix)]}{suffix}'
        counter += 1
    return username


@method_decorator(csrf_protect, name='dispatch')
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        credential = (request.data.get('credential') or '').strip()
        if not credential:
            return Response({'error': 'Google credential is required.'}, status=status.HTTP_400_BAD_REQUEST)

        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or ''
        if not client_id:
            return Response({'error': 'Google sign-in is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            payload = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                client_id,
            )
        except ValueError:
            return Response({'error': 'Invalid Google credential.'}, status=status.HTTP_401_UNAUTHORIZED)

        google_sub = payload.get('sub')
        email = (payload.get('email') or '').strip().lower()
        # Do not treat arbitrary truthy values (for example the string "false")
        # as proof that Google verified the address.
        email_verified = payload.get('email_verified') is True
        # Intentionally ignore Google's "picture" claim.
        # CodeSwitch avatars must only come from explicit user uploads to user.avatar.

        if not google_sub or not email:
            return Response({'error': 'Google credential is missing required account details.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not email_verified:
            return Response({'error': 'Google email must be verified.'}, status=status.HTTP_403_FORBIDDEN)

        user = User.objects.filter(google_sub=google_sub).first()
        if user is None:
            existing = User.objects.filter(email__iexact=email).first()
            if existing:
                if existing.google_sub and existing.google_sub != google_sub:
                    return Response(
                        {'error': 'This email is already linked to another Google account.'},
                        status=status.HTTP_409_CONFLICT,
                    )
                explicitly_linking_current_user = (
                    request.user.is_authenticated and request.user.pk == existing.pk
                )
                if not existing.email_verified and not explicitly_linking_current_user:
                    return Response(
                        {
                            'error': (
                                'An account already uses this email. Sign in with its password '
                                'before linking Google.'
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                existing.google_sub = google_sub
                existing.google_email_verified = True
                existing.email_verified = True
                if not existing.first_name and payload.get('given_name'):
                    existing.first_name = payload.get('given_name', '')[:150]
                if not existing.last_name and payload.get('family_name'):
                    existing.last_name = payload.get('family_name', '')[:150]
                existing.save(update_fields=[
                    'google_sub', 'google_email_verified', 'email_verified',
                    'first_name', 'last_name',
                ])
                user = existing
            else:
                user = User(
                    username=_unique_google_username(email),
                    email=email,
                    first_name=(payload.get('given_name') or '')[:150],
                    last_name=(payload.get('family_name') or '')[:150],
                    google_sub=google_sub,
                    google_email_verified=True,
                    email_verified=True,
                )
                user.set_unusable_password()
                user.save()
        elif not user.google_email_verified:
            user.google_email_verified = True
            if (user.email or '').casefold() == email.casefold():
                user.email_verified = True
            user.save(update_fields=['google_email_verified', 'email_verified'])

        refresh = RefreshToken.for_user(user)
        response = Response({'user': UserProfileSerializer(user, context={'request': request}).data})
        _set_auth_cookies(response, refresh)
        return response


@method_decorator(csrf_protect, name='dispatch')
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


@method_decorator(csrf_protect, name='dispatch')
class CookieTokenRefreshView(APIView):
    """
    POST /api/token/refresh/
    Reads the refresh token from the httpOnly cookie, issues a new access token
    (and rotated refresh token), and sets both back as cookies.
    No request body required.
    """
    permission_classes = [AllowAny]
    throttle_classes = [TokenRefreshThrottle]

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
        return Response(UserProfileSerializer(request.user, context={'request': request}).data)


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [CsrfTokenThrottle]

    def get(self, request):
        return Response({'csrf_token': get_token(request)})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [TrackedUserThrottle, ProfileWriteThrottle]

    def get_object(self):
        return self.request.user


class PublicProfileView(APIView):
    """GET /api/profile/<username>/ — Public stats for any user (no auth required)."""
    permission_classes = [AllowAny]
    throttle_classes = [PublicProfileThrottle]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        from converter.models import ConversionHistory
        from learning.models import UserProgress, LearningModule
        from django.db.models import Count, Q, F

        conversion_count = ConversionHistory.objects.filter(user=user).count()
        completed_progress = UserProgress.objects.filter(user=user, completed=True)
        lessons_completed = completed_progress.count()
        languages_used = list(
            ConversionHistory.objects.filter(user=user)
            .values_list('source_language', flat=True)
            .distinct()
        )

        # Count modules where all lessons are completed by this user (single query)
        modules_completed = (
            LearningModule.objects
            .annotate(
                total_lessons=Count('lessons', distinct=True),
                done_lessons=Count(
                    'lessons__userprogress',
                    filter=Q(
                        lessons__userprogress__user=user,
                        lessons__userprogress__completed=True
                    )
                )
            )
            .filter(total_lessons__gt=0, done_lessons__gte=F('total_lessons'))
            .count()
        )

        return Response({
            'username': user.username,
            'avatar': UserProfileSerializer.avatar_representation(user, request),
            'date_joined': user.date_joined,
            'conversion_count': conversion_count,
            'lessons_completed': lessons_completed,
            'modules_completed': modules_completed,
            'languages_used': languages_used,
        })
