from django.urls import path
from users.views import (
    staff_login,
    member_login,
    logout_session,
    change_password,
)

app_name = "auth"

urlpatterns = [
    path("staff/login/", staff_login, name="staff-login"),
    path("member/login/", member_login, name="member-login"),
    path("logout/", logout_session, name="logout"),
    path("change-password/", change_password, name="change-password"),
]
