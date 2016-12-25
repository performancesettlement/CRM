from datatableview import Datatable
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.views.generic.base import RedirectView
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from sundog.components.emarketing.senders.models import Sender
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogDatatableView,
    template_column,
)


class SendersCRUDViewMixin:
    model = Sender

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'menu_page': 'emarketing',
        }

    class form_class(ModelForm):
        class Meta:
            model = Sender

            fields = [
                'name',
                'sender_address',
                'reply_address',
                'bounce_address',
                'smtp_server',
                'smtp_port',
                'smtp_username',
                'smtp_password',
                'smtp_require_tls',
            ]

    class Meta:
        abstract = True


@route(
    regex=r'^emarketing/?$',
    name='emarketing',
)
class EmarketingRedirect(RedirectView):
    query_string = True
    pattern_name = 'emarketing.senders'


@route(
    regex=r'^emarketing/senders/?$',
    name=[
        'emarketing.senders',
        'emarketing.senders.list',
    ],
)
@decorate_view(login_required)
class SendersList(SendersCRUDViewMixin, SundogDatatableView):
    template_name = 'sundog/emarketing/senders/list.html'

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/emarketing/senders/list/actions.html',
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'id',
                'name',
                'sender_address',
                'smtp_server',
            ]


class SendersAJAXFormMixin(SendersCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(
    regex=r'^emarketing/senders/add/ajax/?$',
    name='emarketing.senders.add.ajax',
)
@decorate_view(login_required)
class SendersAddAJAX(SendersAJAXFormMixin, AjaxCreateView):
    pass


@route(
    regex=r'^emarketing/senders/(?P<pk>\d+)(?:/edit)?/?$',
    name='emarketing.senders.edit',
)
@decorate_view(login_required)
class SendersEdit(SendersCRUDViewMixin, UpdateView):
    template_name = 'sundog/emarketing/senders/edit.html'


@route(
    regex=r'^emarketing/senders/(?P<pk>\d+)(?:/edit)?/ajax/?$',
    name='emarketing.senders.edit.ajax',
)
@decorate_view(login_required)
class SendersEditAJAX(SendersAJAXFormMixin, AjaxUpdateView):
    pass


@route(
    regex=r'^emarketing/senders/(?P<pk>\d+)/delete/ajax/$',
    name='emarketing.senders.delete.ajax',
)
@decorate_view(login_required)
class SendersDeleteAJAX(SendersAJAXFormMixin, AjaxDeleteView):
    pass
