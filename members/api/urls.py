from django.urls import path
from members.api.views import (
    MemberListCreateView,
    MemberDetailView,
    PayInitialCapitalView,
    MemberExitView,
)

app_name = "members"

urlpatterns = [
    path("", MemberListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", MemberDetailView.as_view(), name="detail"),
    path(
        "<uuid:pk>/initial-capital/",
        PayInitialCapitalView.as_view(),
        name="initial-capital",
    ),
    path("<uuid:pk>/exit/", MemberExitView.as_view(), name="exit"),
]
