import structlog
from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import User
from apps.accounts.permissions import CountryScoped

from .models import LoanApplication
from .serializers import LoanApplicationCreateSerializer, LoanApplicationDetailSerializer

ONE_ACTIVE_PER_DOCUMENT = "loan_one_active_per_document"

logger = structlog.get_logger("loans")


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


class LoanApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = LoanApplicationDetailSerializer
    permission_classes = [IsAuthenticated, CountryScoped]

    def get_queryset(self):
        # Applications of other countries do not exist for this user: 404, not 403.
        return LoanApplication.objects.filter(country__in=self.request.user.allowed_countries)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if request.user.role == User.Role.ADMIN:
            # Full PII was shown: leave a trace (ids only, never the data).
            logger.info("pii_access", user_id=request.user.id, application_id=str(kwargs["pk"]))
        return response
