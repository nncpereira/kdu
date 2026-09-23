from django.urls import path

from users.views import (
    change_password,
    logout_session,
    member_login,
    staff_login,
)

app_name = "auth"

urlpatterns = [
    path("staff/login/", staff_login, name="staff-login"),
    path("member/login/", member_login, name="member-login"),
    path("logout/", logout_session, name="logout"),
    path("change-password/", change_password, name="change-password"),
]
