from django.contrib.auth.password_validation import validate_password
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from demo.accounts import is_reserved_username

from .models import User, ChildProfile, ParentChildLink, CHILD_LANGUAGE_PREF_CHOICES
from .services import create_parent, create_child_for_parent


# ============================================
# Registration
# ============================================

class ParentRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True, default='')
    birth_year = serializers.IntegerField(required=False, allow_null=True, default=None)

    def validate_username(self, value):
        if is_reserved_username(value):
            raise serializers.ValidationError("This username is reserved.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        return create_parent(validated_data)


# ============================================
# Child Management (parent-authenticated)
# ============================================

class CreateChildSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    nickname = serializers.CharField(max_length=50)
    birth_year = serializers.IntegerField()
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    language_preference = serializers.ChoiceField(
        choices=CHILD_LANGUAGE_PREF_CHOICES,
        default='en',
        required=False,
    )

    def validate_username(self, value):
        if is_reserved_username(value):
            raise serializers.ValidationError("This username is reserved.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_birth_year(self, value):
        age = timezone.now().year - value
        if age < 6 or age > 13:
            raise serializers.ValidationError(
                "Child must be between 6 and 13 years old."
            )
        return value

    def create(self, validated_data):
        parent_profile = self.context['parent_profile']
        return create_child_for_parent(parent_profile, validated_data)


class LinkedChildSerializer(serializers.ModelSerializer):
    """Read-only representation of a child linked to a parent."""
    username = serializers.CharField(source='user.username', read_only=True)
    age = serializers.SerializerMethodField()
    is_active_in_app = serializers.SerializerMethodField()
    last_activity_at = serializers.SerializerMethodField()

    class Meta:
        model = ChildProfile
        fields = [
            'id', 'username', 'nickname', 'gender',
            'birth_year', 'age', 'avatar_visible', 'language_preference',
            'last_seen_at', 'is_active_in_app', 'last_activity_at',
        ]
        read_only_fields = fields

    def get_age(self, obj):
        if obj.birth_year:
            return timezone.now().year - obj.birth_year
        return None

    def get_is_active_in_app(self, obj):
        """True if the child had API activity in the last 5 minutes."""
        if not obj.last_seen_at:
            return False
        delta = timezone.now() - obj.last_seen_at
        return delta.total_seconds() < 300

    def get_last_activity_at(self, obj):
        """Latest conversation activity (message or session start) for this child."""
        from conversation.models import Message, Session

        msg_time = Message.objects.filter(session__child=obj).aggregate(
            m=Max('created_at')
        )['m']
        session_time = Session.objects.filter(child=obj).aggregate(
            m=Max('started_at')
        )['m']
        candidates = [t for t in (msg_time, session_time) if t is not None]
        return max(candidates) if candidates else None


# ============================================
# Profile
# ============================================


class ChildSelfUpdateSerializer(serializers.ModelSerializer):
    """Authenticated child may update their own profile fields."""

    class Meta:
        model = ChildProfile
        fields = ['nickname', 'birth_year', 'language_preference', 'profile_icon']

    def validate_birth_year(self, value):
        if value is None:
            return value
        age = timezone.now().year - value
        if age < 6 or age > 13:
            raise serializers.ValidationError(
                'Age must correspond to 6–13 years old.'
            )
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Role-branched profile: returns different shapes for parent vs child."""
    profile = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_parent', 'is_child', 'profile', 'children']
        read_only_fields = fields

    def get_profile(self, user):
        if user.is_parent and hasattr(user, 'parent_profile'):
            p = user.parent_profile
            return {
                'name': p.name,
                'phone': p.phone,
                'birth_year': p.birth_year,
            }
        if user.is_child and hasattr(user, 'child_profile'):
            c = user.child_profile
            return {
                'nickname': c.nickname,
                'gender': c.gender,
                'birth_year': c.birth_year,
                'avatar_visible': c.avatar_visible,
                'language_preference': c.language_preference,
                'profile_icon': c.profile_icon,
            }
        return None

    def get_children(self, user):
        if not user.is_parent or not hasattr(user, 'parent_profile'):
            return None
        links = ParentChildLink.objects.filter(
            parent=user.parent_profile,
            consent_status='approved',
        ).select_related('child__user')
        children = [link.child for link in links]
        return LinkedChildSerializer(children, many=True).data


# ============================================
# JWT
# ============================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'user_id': self.user.id,
            'username': self.user.username,
            'is_parent': self.user.is_parent,
            'is_child': self.user.is_child,
        })
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_parent'] = user.is_parent
        token['is_child'] = user.is_child
        return token


# ============================================
# Password Reset
# ============================================

class PasswordResetRequestSerializer(serializers.Serializer):
    """Accepts an email address for the forgot-password flow."""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates uid + token + new password for the reset-password flow."""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )


class ChildPasswordChangeSerializer(serializers.Serializer):
    """Authenticated child changes their own password."""
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
