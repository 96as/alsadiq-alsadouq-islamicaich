from django.urls import path

from .views import (
    ChildManagementView,
    ChildPasswordChangeView,
    ChildProfileSelfView,
    CustomTokenObtainPairView,
    LogoutView,
    ParentRegisterView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ThrottledTokenRefreshView,
    UserProfileView,
)

app_name = 'authentication'

urlpatterns = [
    path('register/parent/', ParentRegisterView.as_view(), name='parent_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/child/', ChildProfileSelfView.as_view(), name='child_profile_self'),
    path('profile/child/password/', ChildPasswordChangeView.as_view(), name='child_password_change'),
    path('children/', ChildManagementView.as_view(), name='children'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
