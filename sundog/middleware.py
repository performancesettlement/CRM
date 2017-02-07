import pytz
from django.utils import timezone
from settings import TIME_ZONE


class TimezoneMiddleware(object):
    def process_request(self, request):
        timezone.activate(pytz.timezone(TIME_ZONE))


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
