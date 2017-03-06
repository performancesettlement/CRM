from datatableview import Datatable
from datatableview.helpers import through_filter
from django.contrib.auth.context_processors import PermWrapper
from django.forms.models import ModelForm
from django.template.defaultfilters import date
from django.urls import reverse
from settings import SHORT_DATETIME_FORMAT
from sundog.components.emarketing.senders.models import Sender

from sundog.constants import (
    E_MARKETING_ACCESS_TAB,
    E_MARKETING_EDIT_SENDER,
    E_MARKETING_DELETE_SENDER,
    E_MARKETING_CREATE_SENDER,
)

from sundog.routing import route
from sundog.util.permission import require_permission

from sundog.util.views import (
    SundogAJAXAddView,
    SundogAJAXDeleteView,
    SundogAJAXEditView,
    SundogDatatableView,
    SundogEditView,
    format_column,
    template_column,
)


class SendersCRUDViewMixin:
    model = Sender

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'breadcrumbs': [
                ('E-mail Marketing', reverse('emarketing')),
                ('Senders', reverse('emarketing.senders')),
            ],
            'menu_page': 'emarketing',
        }
        return context

    class form_class(ModelForm):
        class Meta:
            model = Sender

            fields = '''
                name
                sender_address
                reply_address
                bounce_address
                smtp_server
                smtp_port
                smtp_username
                smtp_password
                smtp_require_tls
            '''.split()

    class Meta:
        abstract = True


@route(
    regex=r'''
        ^emarketing
        /senders
        /?$
    ''',
    name='''
        emarketing.senders
        emarketing.senders.list
    '''.split(),
)
@require_permission(E_MARKETING_ACCESS_TAB)
class SendersList(
    SendersCRUDViewMixin,
    SundogDatatableView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'add_url': (
                reverse('emarketing.senders.add.ajax')
                if self.request.user.has_perm(
                    'sundog.e_marketing__create_senders',
                )
                else None
            ),
            'buttons': [
                ('Templates', reverse('emarketing.templates')),
            ],
        }

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/emarketing/senders/list/actions.html',
            context_builder=lambda **kwargs: {
                'perms': PermWrapper(kwargs['view'].request.user),
            },
        )

        created_by_full_name = format_column(
            label='Created by',
            template='{created_by__first_name} {created_by__last_name}',
            fields='''
                created_by__first_name
                created_by__last_name
            '''.split(),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                id
                created_at
                created_by_full_name
                name
                sender_address
                smtp_server
            '''.split()

            ordering = '''
                -created_at
            '''.split()

            processors = {
                'created_at': through_filter(
                    date,
                    arg=SHORT_DATETIME_FORMAT,
                ),
            }


@route(
    regex=r'''
        ^emarketing
        /senders
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='emarketing.senders.edit',
)
@require_permission(E_MARKETING_EDIT_SENDER)
@require_permission(E_MARKETING_ACCESS_TAB)
class SendersEdit(
    SendersCRUDViewMixin,
    SundogEditView,
):
    pass


@route(
    regex=r'''
        ^emarketing
        /senders
        /add
        /ajax
        /?$
    ''',
    name='emarketing.senders.add.ajax',
)
@require_permission(E_MARKETING_CREATE_SENDER)
@require_permission(E_MARKETING_ACCESS_TAB)
class SendersAddAJAX(
    SendersCRUDViewMixin,
    SundogAJAXAddView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@route(
    regex=r'''
        ^emarketing
        /senders
        /(?P<pk>\d+)
        /delete
        /ajax
        /$
    ''',
    name='emarketing.senders.delete.ajax',
)
@require_permission(E_MARKETING_DELETE_SENDER)
@require_permission(E_MARKETING_ACCESS_TAB)
class SendersDeleteAJAX(
    SendersCRUDViewMixin,
    SundogAJAXDeleteView,
):
    pass


@route(
    regex=r'''
        ^emarketing
        /senders
        /(?P<pk>\d+)
        (?:/edit)?
        /ajax
        /?$
    ''',
    name='emarketing.senders.edit.ajax',
)
@require_permission(E_MARKETING_EDIT_SENDER)
@require_permission(E_MARKETING_ACCESS_TAB)
class SendersEditAJAX(
    SendersCRUDViewMixin,
    SundogAJAXEditView,
):
    pass
