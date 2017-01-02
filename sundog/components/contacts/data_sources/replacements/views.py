from datatableview import Datatable
from datatableview.helpers import through_filter
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.template.defaultfilters import date
from django.urls import reverse
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT

from sundog.components.contacts.data_sources.replacements.models import (
    Replacement,
)

from sundog.components.contacts.data_sources.models import DataSource
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


class ReplacementsCRUDViewMixin:
    model = Replacement

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
        return self.data_source

    class form_class(ModelForm):
        class Meta:
            model = Replacement

            fields = '''
                field
                min_value
                max_value
                replace_value
            '''.split()

    class Meta:
        abstract = True


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /replacements
        /?$
    ''',
    name='''
        contacts.data_sources.replacements
        contacts.data_sources.replacements.list
    '''.split(),
)
@decorate_view(login_required)
class ReplacementsList(
    ReplacementsCRUDViewMixin,
    SundogDatatableView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'add_url': reverse(
                viewname='contacts.data_sources.replacements.add.ajax',
                kwargs={
                    'data_source_id': self.get_data_source().pk,
                },
            ),
            'breadcrumbs': [
                ('Contacts', reverse('contacts')),
                ('Data Sources', reverse('contacts.data_sources')),
                (self.get_data_source(), self.get_data_source()),
                (
                    'Replacements',
                    reverse(
                        viewname='contacts.data_sources.replacements',
                        kwargs={
                            'data_source_id': self.get_data_source().pk,
                        },
                    ),
                ),
            ],
        }

    def get_queryset(self):
        return Replacement.objects.filter(
            field__data_source=self.get_data_source(),
        )

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name=(
                'sundog/contacts/data_sources/replacements/list/actions.html'
            ),
            context_builder=(
                lambda view=None, *_, **__: {
                    'data_source': view.get_data_source(),
                }
            ),
        )

        created_by_full_name = format_column(
            label='Created by',
            fields='''
                created_by__first_name
                created_by__last_name
            '''.split(),
            template='{created_by__first_name} {created_by__last_name}',
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                id
                created_at
                created_by_full_name
                field
                min_value
                max_value
                replace_value
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
        /replacements
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='contacts.data_sources.replacements.edit',
)
@decorate_view(login_required)
class ReplacementsEdit(ReplacementsCRUDViewMixin, UpdateView):
    template_name = 'sundog/contacts/data_sources/replacements/edit.html'


class ReplacementsAJAXFormMixin(ReplacementsCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /replacements
        /add
        /ajax
        /?$
    ''',
    name='contacts.data_sources.replacements.add.ajax'
)
@decorate_view(login_required)
class ReplacementsAddAJAX(
    ReplacementsAJAXFormMixin,
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
        /replacements
        /(?P<pk>\d+)
        (?:/edit)
        /ajax
        /?$
    ''',
    name='contacts.data_sources.replacements.edit.ajax',
)
@decorate_view(login_required)
class ReplacementsEditAJAX(ReplacementsAJAXFormMixin, AjaxUpdateView):
    pass


@route(
    regex=r'''
        ^contacts
        /data_sources
        /(?P<data_source_id>\d+)
        /replacements
        /(?P<pk>\d+)
        /delete
        /ajax
        /?$
    ''',
    name='contacts.data_sources.replacements.delete.ajax',
)
@decorate_view(login_required)
class ReplacementsDeleteAJAX(
    ReplacementsAJAXFormMixin,
    AjaxDeleteView,
):
    pass
