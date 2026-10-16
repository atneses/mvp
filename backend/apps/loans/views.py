import structlog
from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import CountryScoped, IsAdmin

from .models import LoanApplication
from .pagination import LoanApplicationCursorPagination
from .serializers import (
    LoanApplicationCreateSerializer,
    LoanApplicationDetailSerializer,
    LoanApplicationFilterSerializer,
    LoanApplicationListSerializer,
    StatusChangeSerializer,
)
from .services import VersionConflictError, change_status
from .states import InvalidTransitionError

ONE_ACTIVE_PER_DOCUMENT = "loan_one_active_per_document"

logger = structlog.get_logger("loans")


class ActiveApplicationExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "There is already an active application for this document."
    default_code = "active_application_exists"


class VersionConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The application was changed by someone else. Reload it and try again."
    default_code = "version_conflict"


class LoanApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CountryScoped]
    pagination_class = LoanApplicationCursorPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LoanApplicationCreateSerializer
        return LoanApplicationListSerializer

    def get_queryset(self):
        queryset = LoanApplication.objects.filter(country__in=self.request.user.allowed_countries)
        if self.request.method != "GET":
            return queryset

        filters = LoanApplicationFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        params = filters.validated_data
        if "country" in params:
            queryset = queryset.filter(country=params["country"])
        if "status" in params:
            queryset = queryset.filter(status=params["status"])
        return queryset

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


class LoanApplicationStatusView(generics.GenericAPIView):
    """Manual status change by an admin."""

    serializer_class = StatusChangeSerializer
    permission_classes = [IsAuthenticated, IsAdmin, CountryScoped]

    def get_queryset(self):
        return LoanApplication.objects.filter(country__in=self.request.user.allowed_countries)

    def patch(self, request, *args, **kwargs):
        application = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        previous = application.status

        try:
            change_status(application, data["to"], data["expected_version"])
        except VersionConflictError:
            raise VersionConflict() from None
        except InvalidTransitionError as error:
            raise ValidationError({"to": [str(error)]}) from None

        logger.info(
            "status_changed_manually",
            application_id=str(application.id),
            user_id=request.user.id,
            previous=previous,
            to=application.status,
            reason=data["reason"],
        )
        return Response(
            {"id": application.id, "status": application.status, "version": application.version}
        )
