from datatableview import Datatable
from datatableview.columns import (
    CompoundColumn,
    DateColumn,
    DisplayColumn,
    TextColumn,
)
from datatableview.helpers import through_filter
from datatableview.views import XEditableDatatableView
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.template.defaultfilters import date, timesince
from django.template.loader import render_to_string
from furl import furl
from settings import SHORT_DATETIME_FORMAT
from sundog.middleware import Responder
from sundog.models import Contact
from sundog.routing import decorate_view, route
from sundog.utils import const


@route(r'^contacts/?$', name='contact.list')
@route(r'^contacts/?$', name='list_contacts')  # FIXME: Replace view name usages
@route(r'^contacts/lists/$', name='new_list')  # FIXME: Create proper view
@route(r'^dataSources/$', name='data_sources')  # FIXME: Create proper view
@decorate_view(login_required)
class ContactList(XEditableDatatableView):
    template_name = 'sundog/contact/list.html'

    model = Contact

    list_labels = {
        'my_contacts': 'My contacts',
        'all_contacts': 'All contacts',
    }

    default_list = 'my_contacts'

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

        type_ = DisplayColumn(
            label='Type',
            processor=const('Debt Settlement'),  # TODO
        )

        full_name = CompoundColumn(
            'Full name',
            sources=[
                TextColumn(source='last_name'),
                TextColumn(source='first_name'),
                TextColumn(source='middle_name'),
            ],
            processor=(
                lambda *args, **kwargs: (
                    [
                        '{last_name}, {first_name} {middle_name}'
                        .format(**locals())
                        for names in [
                            dict(
                                enumerate(
                                    kwargs.get('default_value', [])
                                )
                            )
                        ]
                        for last_name in [names.get(0, '')]
                        for first_name in [names.get(1, '')]
                        for middle_name in [names.get(2, '')]
                    ] or ['']
                )[0]
            ),
        )

        data_source = DisplayColumn(
            label='Data source',
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

        actions = DisplayColumn(
            label='Actions',
            processor=(
                lambda instance, *_, **__:
                    render_to_string(
                        template_name='sundog/contact/list/actions.html',
                        context={
                            'contact_id': instance.contact_id,
                        },
                    )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'type_',
                'created_at',
                'company',
                'assigned_to',
                'full_name',
                'phone_number',
                'email',
                'stage',
                'status',
                'data_source',
                'last_call_activity',
                'time_in_status',
                'actions',
            ]

            ordering = [
                '-created_at',
            ]

            processors = {
                'created_at': through_filter(
                    date,
                    arg=SHORT_DATETIME_FORMAT,
                ),
            }
