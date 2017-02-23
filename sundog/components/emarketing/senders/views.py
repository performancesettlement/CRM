from datatableview import Datatable, DisplayColumn
from datatableview.helpers import through_filter
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.decorators import permission_required
from django.forms.models import ModelForm
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from settings import SHORT_DATETIME_FORMAT
from sundog.components.emarketing.senders.models import Sender
from sundog.constants import E_MARKETING_ACCESS_TAB, E_MARKETING_EDIT_SENDER, E_MARKETING_DELETE_SENDER, \
    E_MARKETING_CREATE_SENDER
from sundog.routing import route, decorate_view
from sundog.util.permission import get_permission_codename

from sundog.util.views import (
    SundogAJAXAddView,
    SundogAJAXDeleteView,
    SundogAJAXEditView,
    SundogDatatableView,
    SundogEditView,
    format_column,
)


class SendersCRUDViewMixin:
    model = Sender

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'emarketing'
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
@decorate_view(permission_required(get_permission_codename(E_MARKETING_ACCESS_TAB), 'forbidden'))
class SendersList(
    SendersCRUDViewMixin,
    SundogDatatableView,
):

    template_name = 'sundog/emarketing/senders/list/list.html'

    class datatable_class(Datatable):

        actions = DisplayColumn(
            label='Actions',
            processor=(
                lambda instance, *_, **kwargs:
                render_to_string(
                    template_name='sundog/emarketing/senders/list/actions.html',
                    context={
                        'instance': instance,
                        'perms': PermWrapper(kwargs['view'].request.user),
                    },
                )
            ),
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
@decorate_view(permission_required(get_permission_codename(E_MARKETING_EDIT_SENDER), 'forbidden'))
@decorate_view(permission_required(get_permission_codename(E_MARKETING_ACCESS_TAB), 'forbidden'))
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
@decorate_view(permission_required(get_permission_codename(E_MARKETING_CREATE_SENDER), 'forbidden'))
@decorate_view(permission_required(get_permission_codename(E_MARKETING_ACCESS_TAB), 'forbidden'))
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
@decorate_view(permission_required(get_permission_codename(E_MARKETING_DELETE_SENDER), 'forbidden'))
@decorate_view(permission_required(get_permission_codename(E_MARKETING_ACCESS_TAB), 'forbidden'))
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
@decorate_view(permission_required(get_permission_codename(E_MARKETING_EDIT_SENDER), 'forbidden'))
@decorate_view(permission_required(get_permission_codename(E_MARKETING_ACCESS_TAB), 'forbidden'))
class SendersEditAJAX(
    SendersCRUDViewMixin,
    SundogAJAXEditView,
):
    pass
