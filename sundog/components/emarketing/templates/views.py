from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.template.defaultfilters import date
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.emarketing.templates.models import EmailTemplate
from sundog.routing import decorate_view, route

from sundog.util.views import (
    SundogDatatableView,
    format_column,
    template_column,
)


class EmailTemplatesCRUDViewMixin:
    model = EmailTemplate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'menu_page': 'emarketing',
        }

    class form_class(ModelForm):

        class Meta:
            model = EmailTemplate

            fields = [
                'campaign_title',
                'email_subject',
                'category',
                'html_template',
                'text_template',
            ]

            widgets = {
                'category': Select(
                    attrs={
                        'class': 'selectpicker',
                    },
                ),
            }

    class Meta:
        abstract = True


@route(
    r'^emarketing/templates/?$',
    name=[
        'emarketing.templates',
        'emarketing.templates.list',
    ]
)
@decorate_view(login_required)
class EmailTemplatesList(EmailTemplatesCRUDViewMixin, SundogDatatableView):
    template_name = 'sundog/emarketing/templates/list.html'

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/emarketing/templates/list/actions.html',
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
                'campaign_title',
                'email_subject',
                'category',
            ]

            ordering = [
                '-created_at',
            ]

            processors = {
                'created_at': through_filter(
                    date,
                    arg=SHORT_DATETIME_FORMAT,
                ),
                'category': make_processor(
                    lambda category: (
                        EmailTemplate.CATEGORY_CHOICES_DICT[category]
                    ),
                ),
            }


class EmailTemplatesAJAXFormMixin(EmailTemplatesCRUDViewMixin):
    template_name = 'sundog/base/fm_form.html'


@route(
    regex=r'^emarketing/templates/add/ajax/?$',
    name='emarketing.templates.add.ajax',
)
@decorate_view(login_required)
class EmailTemplatesAddAJAX(EmailTemplatesAJAXFormMixin, AjaxCreateView):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@route(
    regex=r'^emarketing/templates/(?P<pk>\d+)(?:/edit)?/?$',
    name='emarketing.templates.edit',
)
@decorate_view(login_required)
class EmailTemplatesEdit(EmailTemplatesCRUDViewMixin, UpdateView):
    template_name = 'sundog/emarketing/templates/edit.html'


@route(
    regex=r'^emarketing/templates/(?P<pk>\d+)(?:/edit)/ajax/?$',
    name='emarketing.templates.edit.ajax',
)
@decorate_view(login_required)
class EmailTemplatesEditAJAX(EmailTemplatesAJAXFormMixin, AjaxUpdateView):
    pass


@route(
    regex=r'^emarketing/templates/(?P<pk>\d+)/delete/ajax/$',
    name='emarketing.templates.delete.ajax',
)
@decorate_view(login_required)
class EmailTemplatesDeleteAJAX(EmailTemplatesAJAXFormMixin, AjaxDeleteView):
    pass
