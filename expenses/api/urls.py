from django.urls import path

from expenses.api.views import ExpenseDetailView, ExpenseListCreateView

app_name = "expenses"

urlpatterns = [
    path("", ExpenseListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", ExpenseDetailView.as_view(), name="detail"),
]
