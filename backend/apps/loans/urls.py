from django.urls import path

from .views import LoanApplicationCreateView, LoanApplicationDetailView

urlpatterns = [
    path("loan-applications", LoanApplicationCreateView.as_view(), name="loan-application-create"),
    path(
        "loan-applications/<uuid:pk>",
        LoanApplicationDetailView.as_view(),
        name="loan-application-detail",
    ),
]
