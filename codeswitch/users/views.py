from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


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
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data,
            })
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid or already blacklisted token.'}, status=status.HTTP_400_BAD_REQUEST)


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
