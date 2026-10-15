"""DRF permissions: by role and by country."""

from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role == User.Role.ADMIN


class CountryScoped(BasePermission):
    """The user may only act on countries listed in allowed_countries.

    - On create: checks the "country" sent in the body.
    - On a single object: checks obj.country.
    Lists are not covered here; their querysets filter by allowed_countries.
    """

    def has_permission(self, request, view):
        country = request.data.get("country")
        if country is None:
            return True
        return request.user.can_access_country(country)

    def has_object_permission(self, request, view, obj):
        return request.user.can_access_country(obj.country)
