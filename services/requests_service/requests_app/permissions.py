from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows request authors to read/update their own requests while everyone else
    only has read access. The actual authentication/authorization layer can be
    plugged in later; for now we rely on the view to provide `request.user`.
    """

    def has_object_permission(self, request, view, obj) -> bool:  # pragma: no cover
        if request.method in permissions.SAFE_METHODS:
            return True
        author_id = getattr(obj, "tg_user_id", None)
        requester_id = getattr(request.user, "telegram_id", None)
        return author_id and requester_id and author_id == requester_id

