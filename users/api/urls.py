from django.urls import path
from users.api.views import MeView, ChangePasswordView

app_name = "users"

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change-password"),
]
