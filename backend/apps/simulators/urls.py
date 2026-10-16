from django.urls import path

from . import views

urlpatterns = [
    path("es/bank-profile", views.spain_bank_profile),
    path("mx/bank-profile", views.mexico_bank_profile),
    path("webhook", views.webhook_receiver),
]
