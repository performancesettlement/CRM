from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.template.defaultfilters import date as date_filter
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.contacts.data_sources.models import DataSource
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


class DataSourcesCRUDViewMixin:
    model = DataSource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
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
                assigning_on
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
                # TODO: assigned_to is ManyToManyField
                **{
                    field: Select(
                        attrs={
                            'class': 'selectpicker',
                        },
                    )
                    for field in '''
                        type
                        file_type
                        status
                        campaign

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
@decorate_view(login_required)
class DataSourcesList(DataSourcesCRUDViewMixin, SundogDatatableView):
    template_name = 'sundog/contacts/data_sources/list.html'

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
@decorate_view(login_required)
class DataSourcesEdit(DataSourcesCRUDViewMixin, UpdateView):
    template_name = 'sundog/contacts/data_sources/edit.html'


class DataSourcesAJAXFormMixin(DataSourcesCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


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
@decorate_view(login_required)
class DataSourcesAddAJAX(DataSourcesAJAXFormMixin, AjaxCreateView):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


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
@decorate_view(login_required)
class DataSourcesEditAJAX(DataSourcesAJAXFormMixin, AjaxUpdateView):
    pass


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
@decorate_view(login_required)
class DataSourcesDeleteAJAX(DataSourcesAJAXFormMixin, AjaxDeleteView):
    pass
