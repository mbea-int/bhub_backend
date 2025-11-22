from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Only admin users have permission"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsBusinessOwner(permissions.BasePermission):
    """User must be the owner of the business"""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsBusinessOwnerOfPost(permissions.BasePermission):
    """User must be the owner of the business that created the post"""

    def has_object_permission(self, request, view, obj):
        return obj.business.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object owner can edit, others can only read"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class GuestReadOnly(permissions.BasePermission):
    """Allow guests to read only"""

    def has_permission(self, request, view):
        # Guests can only GET
        if request.user.is_authenticated and hasattr(request.user, 'is_guest'):
            return request.method in permissions.SAFE_METHODS
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and hasattr(request.user, 'is_guest'):
            return request.method in permissions.SAFE_METHODS
        return True

