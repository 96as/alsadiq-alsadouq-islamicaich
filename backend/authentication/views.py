from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from config.throttling import SharedScopedRateThrottle
from demo.accounts import NotDemoAccount

from .models import ChildProfile, ParentChildLink, User
from .permissions import IsChild, IsParent
from .services import find_reset_user
from .throttles import PasswordResetEmailThrottle
from .serializers import (
    ChildSelfUpdateSerializer,
    ChildPasswordChangeSerializer,
    CreateChildSerializer,
    CustomTokenObtainPairSerializer,
    LinkedChildSerializer,
    ParentRegistrationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
)


class ParentRegisterView(generics.CreateAPIView):
    serializer_class = ParentRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SharedScopedRateThrottle] # rate limiting for registration max 3 requests/minute from the same IP (from settings.py)
    throttle_scope = 'registration'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'detail': 'Parent registered successfully.', 'user_id': user.id},
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [SharedScopedRateThrottle] # max 5 requests/minute. 
    # This is the brute-force protection on the login endpoint.
    throttle_scope = 'auth'


class ThrottledTokenRefreshView(TokenRefreshView):
    """Token refresh in its own per-IP throttle bucket (it used to share the anonymous one)."""
    throttle_classes = [SharedScopedRateThrottle]
    throttle_scope = 'token_refresh'


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Logged out successfully.'},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChildProfileSelfView(generics.GenericAPIView):
    """PATCH — child updates nickname, birth year, language, profile icon."""

    permission_classes = [IsAuthenticated, IsChild]
    serializer_class = ChildSelfUpdateSerializer

    def patch(self, request, *args, **kwargs):
        profile = request.user.child_profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class ChildPasswordChangeView(generics.GenericAPIView):
    """POST — authenticated child changes their own password."""

    serializer_class = ChildPasswordChangeSerializer
    # Shared demo children never get a password (it would outlast the lease).
    permission_classes = [IsAuthenticated, IsChild, NotDemoAccount]
    throttle_classes = [SharedScopedRateThrottle]
    throttle_scope = 'password_change'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response(
            {'detail': 'Password updated successfully.'},
            status=status.HTTP_200_OK,
        )


class ChildManagementView(generics.ListCreateAPIView):
    """
    GET  → list children linked to the authenticated parent.
    POST → create a new child account linked to the authenticated parent.
    """
    # A shared demo parent can list its child but not add new ones.
    permission_classes = [IsAuthenticated, IsParent, NotDemoAccount]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateChildSerializer
        return LinkedChildSerializer

    def get_queryset(self):
        parent_profile = self.request.user.parent_profile
        child_ids = ParentChildLink.objects.filter(
            parent=parent_profile,
            consent_status='approved',
        ).values_list('child_id', flat=True)
        return ChildProfile.objects.filter(
            id__in=child_ids,
        ).select_related('user')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['parent_profile'] = self.request.user.parent_profile
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        child_profile = serializer.save()
        return Response(
            {
                'detail': 'Child account created successfully.',
                'child': LinkedChildSerializer(child_profile).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================
# Password Reset (Parent — email-based)
# ============================================

class PasswordResetRequestView(generics.GenericAPIView):
    """POST /api/auth/password-reset/

    Accepts { email } and sends a password-reset email with a one-time link.
    Always returns 200 regardless of whether the email exists (prevents enumeration).
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SharedScopedRateThrottle, PasswordResetEmailThrottle]
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # .first(): accounts that differ only by email case must not turn this into a 500.
        user = find_reset_user(email)
        if user is None:
            # Return success anyway to prevent email enumeration.
            return Response(
                {'detail': 'If an account with that email exists, a reset link has been sent.'},
                status=status.HTTP_200_OK,
            )

        # Generate HMAC token (tied to user pk + password hash + timestamp).
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        reset_link = f'{frontend_url}/reset-password/{uid}/{token}'

        send_mail(
            subject='Reset your Al-Sadiq Al-Sadouq password',
            message=(
                f'Hello {user.first_name or user.username},\n\n'
                f'We received a request to reset your password. '
                f'Click the link below to set a new password:\n\n'
                f'{reset_link}\n\n'
                f'This link will expire in 1 hour.\n\n'
                f'If you did not request this, you can safely ignore this email.\n\n'
                f'— Al-Sadiq Al-Sadouq Team'
            ),
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            {'detail': 'If an account with that email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """POST /api/auth/password-reset/confirm/

    Accepts { uid, token, new_password } and resets the password if the token is valid.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SharedScopedRateThrottle]
    throttle_scope = 'password_reset_confirm'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {'detail': 'Password has been reset successfully.'},
            status=status.HTTP_200_OK,
        )

