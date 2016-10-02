from ckeditor.fields import RichTextField
from datatableview import Datatable
from datatableview.columns import DisplayColumn
from datatableview.helpers import make_processor, through_filter
from datatableview.views import XEditableDatatableView
from django.contrib.auth.decorators import login_required
from django.db.models import CharField, DateTimeField, Model
from django.forms.models import modelform_factory
from django.forms.widgets import SelectMultiple
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView
from multiselectfield import MultiSelectField
from settings import SHORT_DATETIME_FORMAT
from sundog.models import NONE_CHOICE_LABEL
from sundog.routing import decorate_view, route


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
        ('AA', 'AA-Armed Forces Americas'),
        ('AE', 'AE-Armed Forces Other'),
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AS', 'American Samoa'),
        ('AP', 'AP-Armed Forces Pacific'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('NSW', 'AU-New South Wales'),
        ('ANT', 'AU-Northern Territory'),
        ('QLD', 'AU-Queensland'),
        ('SA', 'AU-South Australia'),
        ('TAS', 'AU-Tasmania'),
        ('VIC', 'AU-Victoria'),
        ('WAU', 'AU-Western Australia'),
        ('CA', 'California'),
        ('AB', 'Canada-Alberta'),
        ('BC', 'Canada-British Columbia'),
        ('MB', 'Canada-Manitoba'),
        ('NB', 'Canada-New Brunswick'),
        ('NL', 'Canada-Newfoundland'),
        ('NT', 'Canada-Northwest Territories'),
        ('NS', 'Canada-Nova Scotia'),
        ('NU', 'Canada-Nunavet'),
        ('ON', 'Canada-Ontario'),
        ('PE', 'Canada-Prince Edward Island'),
        ('QC', 'Canada-Quebec'),
        ('SK', 'Canada-Saskatchewan'),
        ('YT', 'Canada-Yukon'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('DC', 'District of Columbia'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('GU', 'Guam'),
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
        ('PR', 'Puerto Rico'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('VI', 'U.S. Virgin Islands'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    )
    STATE_CHOICES_DICT = dict(STATE_CHOICES)

    title = CharField(max_length=500)
    created_at = DateTimeField(auto_now_add=True)
    type = CharField(max_length=50, choices=TYPE_CHOICES)
    state = MultiSelectField(choices=STATE_CHOICES)
    template_body = RichTextField()

    def get_absolute_url(self):
        return reverse('document.edit', args=[str(self.id)])


class DocumentCRUDViewMixin:
    model = Document

    form_class = modelform_factory(
        model,
        fields=[
            'title',
            'type',
            'state',
            'template_body',
        ],
        widgets={
            "state": SelectMultiple(
                attrs={
                    'class': 'ui fluid dropdown'
                },
            ),
        },
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_page'] = 'documents'
        return context

    class Meta:
        abstract = True


@route(r'^documents/$', name='document.list')
@decorate_view(login_required)
class DocumentList(DocumentCRUDViewMixin, XEditableDatatableView):

    class datatable_class(Datatable):

        actions = DisplayColumn(
            label='Actions',
            processor=(
                lambda instance, *_, **__:
                    render_to_string(
                        template_name='sundog/document_list/actions.html',
                        context={
                            'document_id': instance.id,
                        },
                    )
            ),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = [
                'id',
                'created_at',
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


@route(r'^documents/add/?$', name='document.add')
@decorate_view(login_required)
class DocumentCreate(DocumentCRUDViewMixin, CreateView):
    pass


@route(r'^documents/(?P<pk>\d+)/?$', name='document.edit')
@decorate_view(login_required)
class DocumentUpdate(DocumentCRUDViewMixin, UpdateView):
    pass


# TODO: document.delete
