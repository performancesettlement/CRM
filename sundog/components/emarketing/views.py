from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from sundog.routing import decorate_view, route


@route(
    regex=r'''
        ^emarketing
        /?$
    ''',
    name='emarketing',
)
@decorate_view(login_required)
class EmarketingRedirect(RedirectView):
    query_string = True
    pattern_name = 'emarketing.templates'
