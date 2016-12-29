from datatableview import Datatable
from datatableview.helpers import through_filter
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.template.defaultfilters import date
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.contacts.data_sources.fields.models import Field
from sundog.components.contacts.data_sources.models import DataSource
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


class FieldsCRUDViewMixin:
    model = Field

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'menu_page': 'contacts',
            'data_source': self.get_data_source(),
        }

    def get_data_source(self):
        if not hasattr(self, 'data_source') or not self.data_source:
            self.data_source = DataSource.objects.get(
                pk=self.kwargs['data_source_id'],
            )
        return self.contact

    class form_class(ModelForm):
        class Meta:
            model = Field

            fields = '''
                name
                maps_to
            '''.split()

            widgets = {
                'maps_to': Select(
                    attrs={
                        'class': 'selectpicker',
                        'data-live-search': 'true',
                    },
                ),
            }

    class Meta:
        abstract = True


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /fields
        /?$
    ''',
    name='''
        contacts.data_sources.fields
        contacts.data_sources.fields.list
    '''.split(),
)
@decorate_view(login_required)
class FieldsList(
    FieldsCRUDViewMixin,
    SundogDatatableView,
):
    template_name = 'sundog/contacts/data_sources/fields/list.html'

    def get_queryset(self):
        return Field.objects.filter(
            data_source=self.get_data_source(),
        )

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name=(
                'sundog/contacts/data_sources/fields/list/actions.html'
            ),
            context_builder=(
                lambda view=None, *_, **__: {
                    'data_source': view.get_data_source(),
                }
            ),
        )

        created_by_full_name = format_column(
            label='Created by',
            fields=[
                'created_by__first_name',
                'created_by__last_name',
            ],
            template='{created_by__first_name} {created_by__last_name}',
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                id
                created_at
                created_by_full_name
                name
                maps_to
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


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /fields
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='contacts.data_sources.fields.edit',
)
@decorate_view(login_required)
class FieldsEdit(FieldsCRUDViewMixin, UpdateView):
    template_name = 'sundog/contacts/data_sources/fields/edit.html'


class FieldsAJAXFormMixin(FieldsCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /fields
        /add
        /ajax
        /?$
    ''',
    name='contacts.data_sources.fields.add.ajax'
)
@decorate_view(login_required)
class FieldsAddAJAX(
    FieldsAJAXFormMixin,
    AjaxCreateView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.data_source = self.get_data_source()
        return super().form_valid(form)


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /fields
        /(?P<pk>\d+)
        (?:/edit)
        /ajax
        /?$
    ''',
    name='contacts.data_sources.fields.edit.ajax',
)
@decorate_view(login_required)
class FieldsEditAJAX(FieldsAJAXFormMixin, AjaxUpdateView):
    pass


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /fields
        /(?P<pk>\d+)
        /delete
        /ajax
        /?$
    ''',
    name='contacts.data_sources.fields.delete.ajax',
)
@decorate_view(login_required)
class FieldsDeleteAJAX(
    FieldsAJAXFormMixin,
    AjaxDeleteView,
):
    pass
