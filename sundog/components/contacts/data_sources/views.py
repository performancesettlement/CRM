from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select, SelectMultiple
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from settings import SHORT_DATETIME_FORMAT
from sundog.components.contacts.data_sources.models import DataSource
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogAJAXAddView,
    SundogAJAXDeleteView,
    SundogAJAXEditView,
    SundogDatatableView,
    SundogEditView,
    format_column,
    template_column,
)


class DataSourcesCRUDViewMixin:
    model = DataSource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'breadcrumbs': [
                ('Contacts', reverse('contacts')),
                ('Data Sources', reverse('contacts.data_sources')),
            ],
            'menu_page': 'contacts',
        }

    class form_class(ModelForm):
        class Meta:
            model = DataSource

            fields = '''
                name
                type
                file_type
                status
                campaign
                enabled
                public
                assigned_to
                notification

                company
                marketing_company
                servicing_company
                law_firm
                lead_vendor
                partner

                negotiator
                sales_manager
                client_services_representative
                sales
                processor
                sales_lns
                supervisor
                attorney
                lendstreet
                manager
                abe
            '''.split()

            widgets = {
                'assigned_to': SelectMultiple(
                    attrs={
                        'class': 'selectpicker',
                        'data-actions-box': 'true',
                        'data-live-search': 'true',
                    },
                ),
                **{
                    field: Select(
                        attrs={
                            'class': 'selectpicker',
                            'data-live-search': 'true',
                        },
                    )
                    for field in '''
                        type
                        file_type
                        status
                        campaign
                        notification

                        company
                        marketing_company
                        servicing_company
                        law_firm
                        lead_vendor
                        partner

                        negotiator
                        sales_manager
                        client_services_representative
                        sales
                        processor
                        sales_lns
                        supervisor
                        attorney
                        lendstreet
                        manager
                        abe
                    '''.split()
                },
            }

    class Meta:
        abstract = True


@route(
    regex=r'''
        ^contacts
        /data_sources
        /?$
    ''',
    name='''
        contacts.data_sources
        contacts.data_sources.list
    '''.split(),
)
class DataSourcesList(
    DataSourcesCRUDViewMixin,
    SundogDatatableView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'add_url': reverse('contacts.data_sources.add.ajax'),
        }

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/contacts/data_sources/list/actions.html',
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
                type
                file_type
                status
                campaign
            '''.split()

            ordering = '''
                -created_at
            '''.split()

            processors = {
                'created_at': through_filter(
                    date_filter,
                    arg=SHORT_DATETIME_FORMAT,
                ),
                'file_type': make_processor(
                    lambda file_type:
                        DataSource.FILE_TYPE_CHOICES_DICT[file_type]
                ),
                'type': make_processor(
                    lambda type:
                        DataSource.TYPE_CHOICES_DICT[type]
                ),
            }


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='contacts.data_sources.edit',
)
class DataSourcesEdit(
    DataSourcesCRUDViewMixin,
    SundogEditView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'buttons': [
                (
                    'Edit Fields',
                    reverse(
                        viewname='contacts.data_sources.fields',
                        kwargs={
                            'data_source_id': context['object'].pk,
                        },
                    ),
                ),
                (
                    'Edit Replacements',
                    reverse(
                        viewname='contacts.data_sources.replacements',
                        kwargs={
                            'data_source_id': context['object'].pk,
                        },
                    ),
                ),
            ],
        }


@route(
    regex=r'''
        ^contacts
        /data_sources
        /add
        /ajax
        /?$
    ''',
    name='contacts.data_sources.add.ajax',
)
class DataSourcesAddAJAX(
    DataSourcesCRUDViewMixin,
    SundogAJAXAddView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<pk>\d+)
        /delete
        /ajax
        /?$
    ''',
    name='contacts.data_sources.delete.ajax',
)
class DataSourcesDeleteAJAX(
    DataSourcesCRUDViewMixin,
    SundogAJAXDeleteView,
):
    pass


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<pk>\d+)
        (?:/edit)?
        /ajax
        /?$
    ''',
    name='contacts.data_sources.edit.ajax',
)
class DataSourcesEditAJAX(
    DataSourcesCRUDViewMixin,
    SundogAJAXEditView,
):
    pass
