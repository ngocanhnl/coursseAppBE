from rest_framework import permissions


class CommentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_permission(request, view) and request.user == obj.user


class IsHLV(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        print(request.user.role)
        return request.user.role == 'hlv' or request.user.role == 'admin'