from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.core.handlers.wsgi import WSGIRequest


def bypass_impersonation_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator that bypasses login requirements when impersonating an user.

    :param function:
    :param redirect_field_name:
    :param login_url:
    :return:
    """

    def decorator(*args, **kwargs):
        request = None
        if args:
            request = args[0]
        if isinstance(request, WSGIRequest) and hasattr(request, 'user_impersonator'):
            return function(*args, **kwargs)
        else:
            return login_required(
                function=function, redirect_field_name=redirect_field_name, login_url=login_url)(*args, **kwargs)
    return decorator

