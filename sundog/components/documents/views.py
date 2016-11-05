from datatableview import Datatable
from datatableview.columns import CompoundColumn, DisplayColumn, TextColumn
from datatableview.helpers import make_processor, through_filter
from datatableview.views import XEditableDatatableView
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select, SelectMultiple
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.documents.models import Document
from sundog.routing import decorate_view, route
from sundog.utils import PDFView, format_column, template_column


class DocumentsCRUDViewMixin:
    model = Document

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'documents'
        return context

    class form_class(ModelForm):
        class Meta:
            model = Document

            fields = [
                'title',
                'type',
                'state',
                'template_body',
            ]

            widgets = {
                'state': SelectMultiple(
                    attrs={
                        'class': 'selectpicker',
                        'data-actions-box': 'true',
                        'data-live-search': 'true',
                    },
                ),
                'type': Select(
                    attrs={
                        'class': 'selectpicker',
                        'data-live-search': 'true',
                    },
                ),
            }

    class Meta:
        abstract = True


@route(
    r'^documents/$',
    name=[
        'documents',
        'documents.list',
    ]
)
@decorate_view(login_required)
class DocumentsList(DocumentsCRUDViewMixin, XEditableDatatableView):
    template_name = 'sundog/documents/list.html'

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/documents/list/actions.html',
        )

        created_by_full_name = format_column(
            label='Created by',
            template='{created_by__first_name} {created_by__last_name}',
            fields=[
                'created_by__first_name',
                'created_by__last_name',
            ],
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'id',
                'created_at',
                'created_by_full_name',
                'title',
                'type',
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
                'type': make_processor(
                    lambda type: Document.TYPE_CHOICES_DICT[type]
                ),
            }


class DocumentsAJAXFormMixin(DocumentsCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(r'^documents/add/ajax/?$', name='documents.add.ajax')
@decorate_view(login_required)
class DocumentsAddAJAX(DocumentsAJAXFormMixin, AjaxCreateView):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@route(r'^documents/(?P<pk>\d+)(?:/edit)?/?$', name='documents.edit')
@decorate_view(login_required)
class DocumentsEdit(DocumentsCRUDViewMixin, UpdateView):
    template_name = 'sundog/documents/edit.html'


@route(r'^documents/(?P<pk>\d+)(?:/edit)/ajax/?$', name='documents.edit.ajax')
@decorate_view(login_required)
class DocumentsEditAJAX(DocumentsAJAXFormMixin, AjaxUpdateView):
    pass


@route(r'^documents/(?P<pk>\d+)/delete/ajax/$', name='documents.delete.ajax')
@decorate_view(login_required)
class DocumentsDeleteAJAX(DocumentsAJAXFormMixin, AjaxDeleteView):
    pass


@route(r'^documents/(?P<pk>\d+)/preview/pdf/?$', name='documents.preview.pdf')
@decorate_view(login_required)
class DocumentsPreviewPDF(DocumentsCRUDViewMixin, PDFView):
    pass
