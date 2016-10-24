from datatableview import Datatable
from datatableview.columns import CompoundColumn, DisplayColumn, TextColumn
from datatableview.helpers import make_processor, through_filter
from datatableview.views import XEditableDatatableView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import (
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)
from django.forms.models import ModelForm
from django.forms.widgets import Select, SelectMultiple
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from multiselectfield import MultiSelectField
from settings import SHORT_DATETIME_FORMAT
from sundog.models import NONE_CHOICE_LABEL
from sundog.routing import decorate_view, route
from sundog.utils import LongCharField
from tinymce.models import HTMLField


class Document(Model):
    TYPE_CHOICES = (
        (None, NONE_CHOICE_LABEL),
        ('1099c', '1099-C'),
        ('30_day_notice', '30 Day Notice (debt has moved)'),
        ('3rd_party_auth', '3rd Party Speaker Authorization'),
        ('ach_authorization', 'ACH Authorization'),
        ('audio_recording', 'Audio Recording'),
        ('auth_to_comm_with_cred', 'Auth. To Communicate w/ Creditors'),
        ('bank_statements', 'Bank Statements'),
        ('cancellation_letter', 'Cancellation Letter'),
        ('client_correspondence', 'Client Correspondence'),
        ('collector_correspondence', 'Collector Correspondence'),
        ('contract_agreement', 'Contract / Agreement'),
        ('creditor_correspondence', 'Creditor Correspondence'),
        ('credit_report', 'Credit Report'),
        ('custodial_document', 'Custodial Document'),
        ('general', 'General / Misc.'),
        ('hardship_notification', 'Hardship Notification Letter'),
        ('hardship_statement', 'Hardship Statement'),
        ('inc_exp_form', 'Inc/Exp Form'),
        ('legal_document', 'Legal Document'),
        ('legal_solicitation', 'Legal Solicitation Notice'),
        ('power_of_attorney', 'Power Of Attorney'),
        ('quality_control_rec', 'Quality Control Recording'),
        ('settlement_letter', 'Settlement Letter'),
        ('settlement_offer', 'Settlement Offer'),
        ('settlement_payment_confirmation', 'Settlement Payment Confirmation'),
        ('settlement_recording', 'Settlement Recording'),
        ('statement', 'Statement'),
        ('summons', 'Summons'),
        ('term_checker', 'Term Checker'),
        ('unknown_creditor', 'Unknown Creditor'),
        ('voided_check', 'Voided Check'),
    )
    TYPE_CHOICES_DICT = dict(TYPE_CHOICES)

    STATE_CHOICES = (
        ('Armed Forces', (
            ('AA', 'Americas'),
            ('AP', 'Pacific'),
            ('AE', 'Other'),
        )),
        ('Australia', (
            ('NSW', 'New South Wales'),
            ('ANT', 'Northern Territory'),
            ('QLD', 'Queensland'),
            ('SA', 'South Australia'),
            ('TAS', 'Tasmania'),
            ('VIC', 'Victoria'),
            ('WAU', 'Western Australia'),
        )),
        ('Canada', (
            ('AB', 'Alberta'),
            ('BC', 'British Columbia'),
            ('MB', 'Manitoba'),
            ('NB', 'New Brunswick'),
            ('NL', 'Newfoundland'),
            ('NT', 'Northwest Territories'),
            ('NS', 'Nova Scotia'),
            ('NU', 'Nunavet'),
            ('ON', 'Ontario'),
            ('PE', 'Prince Edward Island'),
            ('QC', 'Quebec'),
            ('SK', 'Saskatchewan'),
            ('YT', 'Yukon'),
        )),
        ('U.S. States', (
            ('AL', 'Alabama'),
            ('AK', 'Alaska'),
            ('AZ', 'Arizona'),
            ('AR', 'Arkansas'),
            ('CA', 'California'),
            ('CO', 'Colorado'),
            ('CT', 'Connecticut'),
            ('DE', 'Delaware'),
            ('FL', 'Florida'),
            ('GA', 'Georgia'),
            ('HI', 'Hawaii'),
            ('ID', 'Idaho'),
            ('IL', 'Illinois'),
            ('IN', 'Indiana'),
            ('IA', 'Iowa'),
            ('KS', 'Kansas'),
            ('KY', 'Kentucky'),
            ('LA', 'Louisiana'),
            ('ME', 'Maine'),
            ('MD', 'Maryland'),
            ('MA', 'Massachusetts'),
            ('MI', 'Michigan'),
            ('MN', 'Minnesota'),
            ('MS', 'Mississippi'),
            ('MO', 'Missouri'),
            ('MT', 'Montana'),
            ('NE', 'Nebraska'),
            ('NV', 'Nevada'),
            ('NH', 'New Hampshire'),
            ('NJ', 'New Jersey'),
            ('NM', 'New Mexico'),
            ('NY', 'New York'),
            ('NC', 'North Carolina'),
            ('ND', 'North Dakota'),
            ('OH', 'Ohio'),
            ('OK', 'Oklahoma'),
            ('OR', 'Oregon'),
            ('PA', 'Pennsylvania'),
            ('RI', 'Rhode Island'),
            ('SC', 'South Carolina'),
            ('SD', 'South Dakota'),
            ('TN', 'Tennessee'),
            ('TX', 'Texas'),
            ('UT', 'Utah'),
            ('VT', 'Vermont'),
            ('VA', 'Virginia'),
            ('WA', 'Washington'),
            ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'),
            ('WY', 'Wyoming'),
        )),
        ('U.S. Others', (
            ('AS', 'American Samoa'),
            ('DC', 'District of Columbia'),
            ('GU', 'Guam'),
            ('PR', 'Puerto Rico'),
            ('VI', 'U.S. Virgin Islands'),
        )),
    )
    STATE_CHOICES_DICT = {
        key: value
        for group, choices in STATE_CHOICES
        for key, value in choices
    }

    title = LongCharField()
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(User, on_delete=SET_NULL, blank=True, null=True)
    type = LongCharField(choices=TYPE_CHOICES)

    # FIXME: Work around stupid arbitrary length limits with a very large stupid
    # arbitrary length limit.  A proper fix would require a modified form of the
    # MultiSelectField class based on LongCharField, which could be accomplished
    # easily by forking the django-multiselectfield project and having it depend
    # on a new small package holding the LongCharField definition.
    state = MultiSelectField(choices=STATE_CHOICES, max_length=2**20)

    template_body = HTMLField()

    def get_absolute_url(self):
        return reverse(
            'documents.edit',
            args=[
                self.id,
            ]
        )


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

        actions = DisplayColumn(
            label='Actions',
            processor=(
                lambda instance, *_, **__:
                    render_to_string(
                        template_name='sundog/documents/list/actions.html',
                        context={
                            'document_id': instance.id,
                            'document_title': instance.title,
                        },
                    )
            ),
        )

        created_by_full_name = CompoundColumn(
            'Created by',
            sources=[
                TextColumn(source='created_by__first_name'),
                TextColumn(source='created_by__last_name'),
            ],
            processor=(
                lambda *args, **kwargs: (
                    [
                        '{first_name} {last_name}'
                        .format(**locals())
                        for names in [
                            dict(
                                enumerate(
                                    kwargs.get('default_value', [])
                                )
                            )
                        ]
                        for first_name in [names.get(0, '')]
                        for last_name in [names.get(1, '')]
                    ] or ['']
                )[0]
            ),
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
