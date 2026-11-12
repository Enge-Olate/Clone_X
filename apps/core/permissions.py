from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePemission):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        author = getattr(obj, "author", None) or getattr(obj, "user", None) or obj
        return author == request.user