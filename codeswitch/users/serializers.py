import re
import base64
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


def _check_password_strength(password):
    """Return list of unmet requirement strings. Empty list = password is strong."""
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("at least one lowercase letter")
    if not re.search(r'\d', password):
        errors.append("at least one number")
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("at least one special character (!@#$%...)")
    return errors


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        unmet = _check_password_strength(value)
        if unmet:
            raise serializers.ValidationError(
                f"Password must contain: {', '.join(unmet)}."
            )
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'email_verified', 'first_name', 'last_name', 'bio', 'avatar', 'date_joined')
        read_only_fields = ('id', 'email_verified', 'date_joined')

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()

    @staticmethod
    def avatar_representation(instance, request=None):
        if instance.avatar_blob:
            content_type = instance.avatar_content_type or 'image/png'
            encoded = base64.b64encode(bytes(instance.avatar_blob)).decode('ascii')
            return f'data:{content_type};base64,{encoded}'

        if not instance.avatar:
            return None

        try:
            url = instance.avatar.url
        except ValueError:
            return None

        return request.build_absolute_uri(url) if request else url

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', serializers.empty)
        previous_email = (instance.email or '').casefold()
        instance = super().update(instance, validated_data)

        if 'email' in validated_data and (instance.email or '').casefold() != previous_email:
            instance.email_verified = False
            instance.save(update_fields=['email_verified'])

        if avatar is not serializers.empty:
            if avatar is None:
                instance.avatar_blob = None
                instance.avatar_content_type = ''
                instance.avatar_filename = ''
                if instance.avatar:
                    instance.avatar.delete(save=False)
                instance.avatar = None
            else:
                avatar.seek(0)
                instance.avatar_blob = avatar.read()
                instance.avatar_content_type = getattr(avatar, 'content_type', '') or 'application/octet-stream'
                instance.avatar_filename = getattr(avatar, 'name', '')[:255]
                if instance.avatar:
                    instance.avatar.delete(save=False)
                instance.avatar = None

            instance.save(update_fields=['avatar_blob', 'avatar_content_type', 'avatar_filename', 'avatar'])

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        data['avatar'] = self.avatar_representation(instance, request)
        return data
