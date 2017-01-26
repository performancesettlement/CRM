from codecs import iterdecode
from csv import DictReader
from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.forms.models import ModelForm
from django.forms.widgets import Select, SelectMultiple
from django.http import Http404, HttpResponse
from django.template.defaultfilters import date
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import SingleObjectMixin
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
                assignment_enabled
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
                    date,
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
    template_name = 'sundog/contacts/data_sources/edit.html'

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
            'post_url': self.request.build_absolute_uri(
                self.object.post_url(),
            ),
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

        if form.instance.password:
            u = User()
            u.set_password(form.instance.password)
            form.instance.password = u.password

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


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<pk>\d+)
        /post
        /(?P<key>[a-z0-9-]+)
        /?$
    ''',
    name='contacts.data_sources.post',
    public=True,
)
@decorate_view(csrf_exempt)
class DataSourcesPost(
    DataSourcesCRUDViewMixin,
    SingleObjectMixin,
    View,
):

    def post(self, request, *args, **kwargs):
        data_source = self.object = self.get_object()

        if kwargs['key'] != self.object.key.hex:
            raise Http404

        if self.object.username and self.object.password:
            authenticate_response = HttpResponse()
            authenticate_response.status_code = 401
            authenticate_response['WWW-Authenticate'] = 'Basic'

            user = User(
                username=self.object.username,
                password=self.object.password,
            )

            authorization = request.META.get('HTTP_AUTHORIZATION', None)
            if not authorization:
                return authenticate_response

            method, credentials = authorization.split(' ', 1)
            if method.lower() != 'basic':
                return authenticate_response

            username, password = (
                credentials
                .strip()
                .decode('base64')
                .split(':', 1)
            )
            if not (
                username == user.username and
                user.check_password(password)
            ):
                raise PermissionDenied

        if data_source.type == 'web_form':
            data_source.import_contact(request.POST)
            return HttpResponse(status=201)  # FIXME: add Location header

        elif data_source.type == 'import':

            if 'csv' not in request.FILES:
                return HttpResponse('Missing file argument', status=422)

            for row in DictReader(
                iterdecode(
                    request.FILES['csv'],
                    'utf-8',
                )
            ):
                data_source.import_contact(row),

            # TODO: Send notification e-mails

            return HttpResponse(status=200)
