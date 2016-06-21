import pytz
from django.utils import timezone
from sundog.cache.user.info import get_cache_user


class TimezoneMiddleware(object):
    def process_request(self, request):
        try:
            tzname = request.session.get('django_timezone')
            if tzname:
                timezone.activate(pytz.timezone(tzname))
            else:
                timezone.deactivate()
        except:
            timezone.deactivate()


class ImpersonationMiddleware(object):
    def process_request(self, request):
        user_impersonation = request.session.get('user_impersonation', False)
        if user_impersonation:
            user_impersonated = request.session['user_impersonated']
            user_impersonator = request.session['user_impersonator']
            request.user = get_cache_user(user_impersonated['id'])
            request.user_impersonator = get_cache_user(user_impersonator['id'])
