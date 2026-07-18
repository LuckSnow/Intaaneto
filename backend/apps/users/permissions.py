from rest_framework.permissions import BasePermission


class IsRoleAdmin(BasePermission):
    """Allow only active, verified users with the server-owned admin role."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_verified
            and user.role == 'admin'
        )
