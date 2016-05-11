import pytz
import settings
from django.utils import timezone
import services


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
