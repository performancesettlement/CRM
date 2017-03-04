from django.contrib.auth.decorators import permission_required
from sundog.routing import decorate_view


def get_permission_codename(name):
    return 'sundog.' + name


def require_permission(permission):
    return decorate_view(
        permission_required(
            perm=get_permission_codename(
                name=permission,
            ),
            login_url='forbidden',
        ),
    )
