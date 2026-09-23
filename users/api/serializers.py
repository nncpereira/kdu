from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "must_change_password",
            "created_at",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class StaffUserSerializer(serializers.ModelSerializer):
    """
    Read serializer for staff users. Includes profile fields inline.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    last_login = serializers.DateTimeField(source="user.last_login", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "must_change_password",
            "is_active",
            "last_login",
            "created_at",
        ]


class CreateStaffUserSerializer(serializers.Serializer):
    """
    Write serializer for creating a new staff user + profile in one call.
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    first_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    last_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.Role.choices)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_role(self, value):
        # MEMBER role cannot be created via this endpoint.
        if value == UserProfile.Role.MEMBER:
            raise serializers.ValidationError(
                "MEMBER accounts are auto-provisioned during onboarding."
            )
        return value


class UpdateStaffUserSerializer(serializers.Serializer):
    """
    Write serializer for editing first_name / last_name / email.
    Role is intentionally not editable (segregation of duties).
    """

    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)


class UpdateMyProfileSerializer(serializers.Serializer):
    """
    Fields a user can change about themselves.
    Role, username, and is_active are intentionally excluded.
    """

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
