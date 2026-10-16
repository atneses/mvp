from django.urls import path

from . import views

urlpatterns = [
    path("es/bank-profile", views.spain_bank_profile),
]
