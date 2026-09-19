from django.urls import path
from ledger.api.views import ReversalListCreateView, ReversalDetailView

app_name = "ledger"

urlpatterns = [
    path("reversals/", ReversalListCreateView.as_view(), name="reversal-list-create"),
    path("reversals/<uuid:pk>/", ReversalDetailView.as_view(), name="reversal-detail"),
]
