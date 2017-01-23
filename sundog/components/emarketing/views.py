from django.views.generic.base import RedirectView
from sundog.routing import route


@route(
    regex=r'''
        ^emarketing
        /?$
    ''',
    name='emarketing',
)
class EmarketingRedirect(RedirectView):
    query_string = True
    pattern_name = 'emarketing.templates'
