from django.contrib.auth.models import User
from django.core.cache import cache

USER_CACHE_BASE_KEY = "user_"
USER_CACHE_TIMEOUT = 1800


def _get_user_cache_key(user_id):
    return USER_CACHE_BASE_KEY + str(user_id)


def get_cache_user(user_id):
    user = cache.get(_get_user_cache_key(user_id))
    if not user:
        user = User.objects.get(id=user_id)
        store_cache_user(user)
        return user
    return user


def store_cache_user(user):
    cache.set(_get_user_cache_key(user.id), user, USER_CACHE_TIMEOUT)
