from django.utils.timezone import now
import pytz
from django.utils import timezone
from settings import TIME_ZONE
from sundog.cache.user.info import get_cache_user


class TimezoneMiddleware(object):
    def process_request(self, request):
        timezone.activate(pytz.timezone(TIME_ZONE))


class ImpersonationMiddleware(object):
    def process_request(self, request):
        user_impersonation = request.session.get('user_impersonation', False)
        if user_impersonation:
            user_impersonated = request.session['user_impersonated']
            user_impersonator = request.session['user_impersonator']
            request.user = get_cache_user(user_impersonated['id'])
            request.user_impersonator = get_cache_user(user_impersonator['id'])


class Responder(Exception):
    '''
    Trigger a response in any part of a view by throwing an exception.
    '''
    def __init__(self, responder):
        self.responder = responder


class ExceptionResponderMiddleware:
    def process_exception(self, request, e):
        '''
        This middleware checks for the ForceResponse exception and calls the
        responder function in the exception, passing the request object.
        '''
        if isinstance(e, Responder):
            return e.responder(request)
        raise e
