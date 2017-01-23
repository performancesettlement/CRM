from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.template.defaultfilters import date
from django.urls import reverse
from settings import SHORT_DATETIME_FORMAT
from sundog.components.emarketing.templates.models import EmailTemplate
from sundog.routing import route

from sundog.util.views import (
    SundogAJAXAddView,
    SundogAJAXDeleteView,
    SundogAJAXEditView,
    SundogDatatableView,
    SundogEditView,
    format_column,
    template_column,
)


class EmailTemplatesCRUDViewMixin:
    model = EmailTemplate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'breadcrumbs': [
                ('E-mail Marketing', reverse('emarketing')),
                ('Templates', reverse('emarketing.templates')),
            ],
            'menu_page': 'emarketing',
        }

    class form_class(ModelForm):

        class Meta:
            model = EmailTemplate

            fields = '''
                campaign_title
                email_subject
                category
                html_template
                text_template
            '''.split()

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
    regex=r'''
        ^emarketing
        /templates
        /?$
    ''',
    name='''
        emarketing.templates
        emarketing.templates.list
    '''.split(),
)
class EmailTemplatesList(
    EmailTemplatesCRUDViewMixin,
    SundogDatatableView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'add_url': reverse('emarketing.templates.add.ajax'),
            'buttons': [
                ('Senders', reverse('emarketing.senders')),
            ],
        }

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/emarketing/templates/list/actions.html',
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
                campaign_title
                email_subject
                category
            '''.split()

            ordering = '''
                -created_at
            '''.split()

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


@route(
    regex=r'''
        ^emarketing
        /templates
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='emarketing.templates.edit',
)
class EmailTemplatesEdit(
    EmailTemplatesCRUDViewMixin,
    SundogEditView,
):
    pass


@route(
    regex=r'''
        ^emarketing
        /templates
        /add
        /ajax
        /?$
    ''',
    name='emarketing.templates.add.ajax',
)
class EmailTemplatesAddAJAX(
    EmailTemplatesCRUDViewMixin,
    SundogAJAXAddView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@route(
    regex=r'''
        ^emarketing
        /templates
        /(?P<pk>\d+)
        /delete
        /ajax
        /$
    ''',
    name='emarketing.templates.delete.ajax',
)
class EmailTemplatesDeleteAJAX(
    EmailTemplatesCRUDViewMixin,
    SundogAJAXDeleteView,
):
    pass


@route(
    regex=r'''
        ^emarketing
        /templates
        /(?P<pk>\d+)
        (?:/edit)
        /ajax
        /?$
    ''',
    name='emarketing.templates.edit.ajax',
)
class EmailTemplatesEditAJAX(
    EmailTemplatesCRUDViewMixin,
    SundogAJAXEditView,
):
    pass
