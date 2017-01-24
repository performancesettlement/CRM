from datatableview import Datatable
from datatableview.columns import DateColumn, DisplayColumn, TextColumn
from datatableview.helpers import through_filter
from django.http import Http404
from django.shortcuts import redirect
from django.template.defaultfilters import date, timesince
from furl import furl
from settings import SHORT_DATETIME_FORMAT
from sundog.middleware import Responder
from sundog.models import Contact
from sundog.routing import route
from sundog.util.functional import const

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


@route(
    regex=r'''
        ^contacts
        /?$
    ''',
    # FIXME: Replace list_contacts view name usages with «contacts»
    name='''
        contacts
        contacts.list
        list_contacts
    '''.split(),
)
@route(r'^contacts/lists/$', name='new_list')  # FIXME: Create proper view
class ContactsList(SundogDatatableView):
    template_name = 'sundog/contacts/list.html'

    model = Contact

    list_labels = {
        'my_contacts': 'My contacts',
        'all_contacts': 'All contacts',
    }

    default_list = 'my_contacts'

    searchable_columns = '''
        type_
        created_at
        company
        assigned_to
        full_name
        phone_number
        email
        stage
        status
        lead_source
        last_call_activity
        time_in_status
    '''.split()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'contacts'
        context['list_labels'] = self.list_labels.items()
        context['selected_list'] = self.selected_list
        return context

    def get_datatable(self):
        datatable = super().get_datatable()

        self.selected_list = self.request.GET.get(
            'selected_list',
            self.default_list,
        )

        datatable.url = (
            furl(datatable.url)
            .add(args={'selected_list': self.selected_list})
            .url
        )

        if not self.selected_list:
            raise Responder(
                const(
                    redirect(
                        to=datatable.url,
                        permanent=True,
                    ),
                ),
            )

        if self.selected_list not in self.list_labels.keys():
            raise Http404('No such list: ' + self.selected_list)

        datatable.object_list = (
            datatable.object_list or
            datatable.model.objects.all()
        )

        if self.selected_list == 'my_contacts':
            datatable.object_list = datatable.object_list.filter(
                assigned_to=self.request.user.id,
            )

        return datatable

    class datatable_class(Datatable):

        company = TextColumn(
            label="Company",
            sources=['company__name'],
        )

        type_ = DisplayColumn(
            label='Type',
            processor=const('Debt Settlement'),  # TODO
        )

        full_name = format_column(
            label='Full name',
            template='{last_name}, {first_name} {middle_name}',
            fields='''
                last_name
                first_name
                middle_name
            '''.split(),
        )

        lead_source = DisplayColumn(
            label='Lead source',
            processor=const(''),  # TODO
        )

        last_call_activity = DisplayColumn(
            label='Last call activity',
            processor=const(''),  # TODO
        )

        time_in_status = DateColumn(
            label='Time in status',
            source='last_status_change',
            processor=(
                lambda instance, *_, **__:
                    timesince(instance.last_status_change)
                    if instance.last_status_change
                    else ''
            ),
        )

        actions = template_column(
            label='Actions',
            template_name='sundog/contacts/list/actions.html',
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                type_
                created_at
                company
                assigned_to
                full_name
                phone_number
                email
                stage
                status
                lead_source
                last_call_activity
                time_in_status
                actions
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
