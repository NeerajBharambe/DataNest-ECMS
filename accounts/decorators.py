from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Restrict a view to users whose `role` is in allowed_roles.
    Usage:
        @login_required
        @role_required("ADMIN", "EDITOR")
        def my_view(...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or getattr(user, "role", None) not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


