from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Transaction 모델은 user_id(str) 필드를 가짐
        return str(obj.user_id) == str(request.user.id)
