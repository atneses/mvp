from decimal import Decimal

from rest_framework import serializers

from apps.accounts.models import User
from core.pii import mask_document, mask_name
from countries.base import InvalidDocumentError
from countries.registry import get_plugin

from .models import LoanApplication


class LoanApplicationCreateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    monthly_income = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0.01")
    )
    # Write-only: the response of a creation never echoes PII.
    full_name = serializers.CharField(max_length=200, write_only=True)
    document = serializers.CharField(max_length=32, write_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "country",
            "status",
            "version",
            "amount",
            "currency",
            "monthly_income",
            "full_name",
            "document",
            "created_at",
        ]
        read_only_fields = ["id", "status", "version", "currency", "created_at"]
        # No automatic unique check: the database constraint decides (safe under
        # concurrent requests) and the view turns it into a 409.
        validators = []

    def validate(self, data):
        # Each country validates its own document and sets its own currency.
        plugin = get_plugin(data["country"])
        try:
            data["document"] = plugin.validate_document(data["document"])
        except InvalidDocumentError as error:
            raise serializers.ValidationError({"document": [str(error)]}) from None
        data["currency"] = plugin.currency
        return data


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "country",
            "status",
            "version",
            "amount",
            "currency",
            "monthly_income",
            "full_name",
            "document",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only admins see the full PII; everyone else gets it masked.
        if self.context["request"].user.role != User.Role.ADMIN:
            data["full_name"] = mask_name(instance.full_name)
            data["document"] = mask_document(instance.document)
        return data


class LoanApplicationListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "country",
            "status",
            "amount",
            "currency",
            "full_name",
            "document",
            "created_at",
        ]

    def get_full_name(self, instance):
        return mask_name(instance.full_name)

    def get_document(self, instance):
        return mask_document(instance.document)


class LoanApplicationFilterSerializer(serializers.Serializer):
    country = serializers.CharField(max_length=2, required=False)
    status = serializers.ChoiceField(choices=LoanApplication.Status.choices, required=False)


class StatusChangeSerializer(serializers.Serializer):
    to = serializers.ChoiceField(choices=LoanApplication.Status.choices)
    reason = serializers.CharField(max_length=500)
    expected_version = serializers.IntegerField(min_value=1)
