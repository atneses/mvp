from django.urls import path

from .views import LoanApplicationDetailView, LoanApplicationListCreateView

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
]
