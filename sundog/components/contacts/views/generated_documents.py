from datatableview import Datatable
from datatableview.helpers import through_filter
from datatableview.views import XEditableDatatableView
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.shortcuts import redirect
from django.template.defaultfilters import date
from django.views.generic.detail import BaseDetailView
from fm.views import AjaxCreateView, AjaxDeleteView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.documents.models import GeneratedDocument
from sundog.models import Contact
from sundog.routing import decorate_view, route
from sundog.utils import format_column, template_column


class GeneratedDocumentsCRUDViewMixin:
    model = GeneratedDocument

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'menu_page': 'contacts',
            'contact': self.get_contact(),
        }

    def get_contact(self):
        if not hasattr(self, 'contact') or not self.contact:
            self.contact = Contact.objects.get(
                pk=self.kwargs['contact_id'],
            )
        return self.contact

    class form_class(ModelForm):
        class Meta:
            model = GeneratedDocument

            fields = [
                'title',
                'template',
            ]

            widgets = {
                'template': Select(
                    attrs={
                        'class': 'selectpicker',
                        'data-live-search': 'true',
                    },
                ),
            }

    class Meta:
        abstract = True


@route(
    regex=r'^contacts/(?P<contact_id>\d+)/generated_documents/?$',
    name=[
        'contacts.generated_documents',
        'contacts.generated_documents.list',
    ],
)
@decorate_view(login_required)
class GeneratedDocumentsList(
    GeneratedDocumentsCRUDViewMixin,
    XEditableDatatableView,
):
    template_name = 'sundog/contacts/generated_documents/list.html'

    def get_queryset(self):
        return GeneratedDocument.objects.filter(
            contact=self.get_contact(),
        )

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name=(
                'sundog/contacts/generated_documents/list/actions.html'
            ),
            context_builder=(
                lambda view=None, *_, **__: {
                    'contact': view.contact,
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

            columns = [
                'title',
                'created_at',
                'created_by_full_name',
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


@route(
    regex=r'^contacts/(?P<contact_id>\d+)/generated_documents/(?P<pk>\d+)/view',
    name='contacts.generated_documents.view'
)
@decorate_view(login_required)
class GeneratedDocumentsView(
    GeneratedDocumentsCRUDViewMixin,
    BaseDetailView,
):
    def render_to_response(self, context):
        return redirect(self.object)


class GeneratedDocumentsAJAXFormMixin(GeneratedDocumentsCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(
    regex=r'^contacts/(?P<contact_id>\d+)/generated_documents/add/ajax/?$',
    name='contacts.generated_documents.add.ajax'
)
@decorate_view(login_required)
class GeneratedDocumentsAddAJAX(
    GeneratedDocumentsAJAXFormMixin,
    AjaxCreateView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.contact = self.get_contact()
        return super().form_valid(form)


@route(
    regex=(
        r'^contacts/(?P<contact_id>\d+)/generated_documents/(?P<pk>\d+)/delete'
        r'/ajax/?$'
    ),
    name='contacts.generated_documents.delete.ajax',
)
@decorate_view(login_required)
class GeneratedDocumentsDeleteAJAX(
    GeneratedDocumentsAJAXFormMixin,
    AjaxDeleteView,
):
    pass
