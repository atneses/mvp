from django.urls import path

from .views import (
    LoanApplicationDetailView,
    LoanApplicationListCreateView,
    LoanApplicationStatusView,
)

urlpatterns = [
    path(
        "loan-applications",
        LoanApplicationListCreateView.as_view(),
        name="loan-application-list",
    ),
    path(
        "loan-applications/<uuid:pk>",
        LoanApplicationDetailView.as_view(),
        name="loan-application-detail",
    ),
    path(
        "loan-applications/<uuid:pk>/status",
        LoanApplicationStatusView.as_view(),
        name="loan-application-status",
    ),
]
