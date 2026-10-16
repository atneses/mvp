from django.urls import path

from .views import LoanApplicationCreateView

urlpatterns = [
    path("", LoanApplicationCreateView.as_view(), name="loan-application-create"),
]
