from django.urls import path

from users.api.views import (
    ChangePasswordView,
    MeView,
    StaffUserDetailView,
    StaffUserDisableView,
    StaffUserEnableView,
    StaffUserListCreateView,
    StaffUserResetPasswordView,
)

app_name = "users"

urlpatterns = [
    # Self-service
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change-password"),
    # Superadmin staff management
    path("", StaffUserListCreateView.as_view(), name="staff-list-create"),
    path("<int:pk>/", StaffUserDetailView.as_view(), name="staff-detail"),
    path("<int:pk>/disable/", StaffUserDisableView.as_view(), name="staff-disable"),
    path("<int:pk>/enable/", StaffUserEnableView.as_view(), name="staff-enable"),
    path(
        "<int:pk>/reset-password/",
        StaffUserResetPasswordView.as_view(),
        name="staff-reset-password",
    ),
]
