from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import CountryScoped

from .serializers import LoanApplicationCreateSerializer

ONE_ACTIVE_PER_DOCUMENT = "loan_one_active_per_document"


class ActiveApplicationExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "There is already an active application for this document."
    default_code = "active_application_exists"


class LoanApplicationCreateView(generics.CreateAPIView):
    serializer_class = LoanApplicationCreateSerializer
    permission_classes = [IsAuthenticated, CountryScoped]

    def perform_create(self, serializer):
        try:
            # Own transaction so the connection stays usable after the error.
            with transaction.atomic():
                serializer.save(created_by=self.request.user)
        except IntegrityError as error:
            # Only the "one active application per document" rule becomes a 409.
            if getattr(error.__cause__.diag, "constraint_name", None) == ONE_ACTIVE_PER_DOCUMENT:
                raise ActiveApplicationExists() from None
            raise
