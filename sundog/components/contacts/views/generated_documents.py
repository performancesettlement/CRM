from datatableview import Datatable
from datatableview.helpers import through_filter
from datatableview.views import XEditableDatatableView
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.shortcuts import redirect
from django.template.defaultfilters import date as date_filter
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
                    date_filter,
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

    def default_contact(self):
        return Contact(
            contact_id=-1,
            first_name='Test',
            middle_name='Ing',
            last_name='User',
            previous_name='',
            phone_number='8885551234',
            mobile_number='8887771234',
            email='test.user@example.com',
            birth_date=date(1983, 10, 4),
            identification='000-123-4567',
            marital_status='married',
            co_applicant_first_name='CoTest',
            co_applicant_middle_name='CoIng',
            co_applicant_last_name='CoUser',
            co_applicant_previous_name='Co Previous Name',
            co_applicant_phone_number='8882221234',
            co_applicant_mobile_number='8884441234',
            co_applicant_email='co.test.user@example.com',
            co_applicant_birth_date=date(1984, 11, 5),
            co_applicant_identification='000-765-4321',
            co_applicant_marital_status='divorced',
            dependants='4',
            address_1='123 Fake St.',
            address_2='APT 1',
            city='Chicago',
            state='IL',
            zip_code='60101',
            residential_status='home_owner',
            co_applicant_address_1='321 Fake St.',
            co_applicant_address_2='APT 2',
            co_applicant_city='Newport',
            co_applicant_state='CA',
            co_applicant_zip_code='60103',
            employer='Testing Employer, Inc',
            employment_status='retired',
            position='Senior Manager',
            length_of_employment='20 years',
            work_phone='8886661234',
            co_applicant_employer='Co Testing Employer, Inc',
            co_applicant_employment_status='employed',
            co_applicant_position='Supervisor',
            co_applicant_length_of_employment='5 years',
            co_applicant_work_phone='8883331234',
            hardships='loss_of_employment',
            hardship_description=(
                'I was involved in a major car accident and had to take 3'
                ' months off of work'
            ),
            special_note_1='Test note 1',
            special_note_2='Test note 2',
            special_note_3='Test note 3',
            special_note_4='Test note 4',
            ssn1='000-987-6543',
            ssn2='000-345-6789',
            third_party_speaker_full_name='Test Third Party Speaker',
            third_party_speaker_last_4_of_ssn='1234',
            authorization_form_on_file='yes',
            active=True,
            assigned_to=self.request.user,
            # call_center_representative=ForeignKey(User),                # TODO
            # lead_source=ForeignKey(LeadSource),                         # TODO
            # company=ForeignKey(Company, null=True, blank=True),         # TODO
            # stage=ForeignKey(Stage, blank=True, null=True),             # TODO
            # status=ForeignKey(Status, blank=True, null=True),           # TODO
            last_status_change=date.today(),
            created_at=date.today() - timedelta(days=2),
            updated_at=date.today() - timedelta(days=1),
        )

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
        form.instance.content.save(
            name='{pk}.pdf'.format(  # FIXME: better filename; use title slug
                pk=self.get_contact().pk,
            ),
            content=ContentFile(
                content=(
                    form.instance.template
                    .render(
                        contact=self.get_contact(),
                    )
                    .write_pdf()
                ),
            ),
        )
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
