from argparse import Namespace
from datetime import date, timedelta
from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.apps.registry import Apps
from django.contrib.auth.decorators import login_required
from django.forms.models import ModelForm
from django.forms.widgets import Select, SelectMultiple
from django.template.defaultfilters import date as date_filter
from django.views.generic.edit import UpdateView
from fm.views import AjaxCreateView, AjaxDeleteView, AjaxUpdateView
from settings import SHORT_DATETIME_FORMAT
from sundog.components.documents.models import Document
from sundog.models import (
    Activity,
    BankAccount,
    Company,
    Contact,
    DEBT_SETTLEMENT,
    LeadSource,
    Note,
    Stage,
    Status,
)
from sundog.routing import decorate_view, route
from sundog.utils import (
    PDFView,
    SundogDatatableView,
    format_column,
    template_column,
)


class DocumentsCRUDViewMixin:
    model = Document

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'menu_page': 'documents',
        }

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
class DocumentsList(DocumentsCRUDViewMixin, SundogDatatableView):
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
                    date_filter,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'menu_page': 'documents',
            'contact': self.default_contact(),
        }

    def default_contact(self):

        fake_id = 0

        def get_fake_id():
            nonlocal fake_id
            fake_id -= 1
            return fake_id

        today = date.today()

        contact_id = get_fake_id()

        bank_account = BankAccount(
            routing_number='011103093',
            account_number='123456789012345678901234567890',
            account_type='checking',
            name_on_account='TEST ING USER',
            bank_name='Test Bank',
            address='789 Fake St.',
            city='Avon',
            state='CT',
            zip_code='06001',
            phone='9165550108',
            created_at=today - timedelta(days=4),
            updated_at=today - timedelta(days=3),
        )

        company = Company(
            company_id=get_fake_id(),
            active=True,
            company_type='law_firm',
            parent_company=None,
            name='Testing Company, Inc',
            contact_name='Testing Contact',
            # company_code='',  # TODO
            # ein='',  # TODO
            address='987 Fake St.',
            address_2='APT 9',
            city='Belmont',
            state='CA',
            zip='94002',
            phone='9165550106',
            fax='9165550107',
            email='testing.company@example.com',
            # domain='',  # TODO
            timezone='pacific',
            account_exec='user_test',
            theme='default',
            # upload_logo=FileField(...),  # TODO
            userfield_1='Test user field 1',
            userfield_2='Test user field 2',
            userfield_3='Test user field 3',
            # docusign_api_acct='',  # TODO
            # docusign_api_user='',  # TODO
            # docusign_password='',  # TODO
        )

        lead_source = LeadSource(
            lead_source_id=get_fake_id(),
            name='Test lead source',
        )

        stage = Stage(
            stage_id=-2,
            name='Test stage',
            order=0,
            type=DEBT_SETTLEMENT,
        )

        status = Status(
            status_id=get_fake_id(),
            name='Test status',
            stage=stage,
        )

        # The activities and notes fields of a Contact object are RelatedManager
        # objects, and it's apparently not practical to create a RelatedManager
        # for a fake collection of model instances.  This mocks the parts of the
        # API relevant for the document generation process.  Note the object
        # returned from the mocked all() method of each mocked RelatedManager is
        # not a QuerySet, as it would be when using a proper Contact instance,
        # but is instead just a regular Python list.  No document tag uses any
        # other part of the QuerySet API than simple iteration, so this should
        # not cause any issues for now.
        class FakeContact(Contact):

            activities = Namespace(
                all=lambda: [
                    Activity(
                        activity_id=get_fake_id(),
                        contact_id=contact_id,
                        created_at=today - timedelta(days=1),
                        created_by=self.request.user,
                        type='enrollment',
                        description='Enrollment Plan Saved',
                    ),
                    Activity(
                        activity_id=get_fake_id(),
                        contact_id=contact_id,
                        created_at=today - timedelta(days=2),
                        created_by=self.request.user,
                        type='general',
                        description='Contact Record Created',
                    ),
                ],
            )

            notes = Namespace(
                all=lambda: [
                    Note(
                        note_id=get_fake_id(),
                        contact_id=contact_id,
                        created_at=today - timedelta(days=1),
                        created_by=self.request.user,
                        type='file_note',
                        description='draft was returned for insufficient funds',
                    ),
                    Note(
                        note_id=get_fake_id(),
                        contact_id=contact_id,
                        created_at=today - timedelta(days=2),
                        created_by=self.request.user,
                        type='welcome_call_attempt',
                        description='Welcome call transferred to Lisa',
                    ),
                ],
            )

            # The metaclass for Django models automatically registers all
            # defined model classes into the current Django application.  This
            # is not a regular model that should be registered and accessible to
            # any other part of the application, though.  One way to avoid that
            # is to provide an empty Django application here so that the
            # metaclass registers the model in isolation from the rest of the
            # system.  There is unfortunately no way to entirely prevent
            # registration, as the metaclass registers model classes
            # unconditionally and the Python metaobject protocol does not allow
            # for the FakeContact class to inherit from Contact yet not share
            # its metaclass.  Furthermore, there seems to be no way to use an
            # instance of the Contact class and override the activities
            # attribute other than subclassing; the attribute cannot be assigned
            # directly.
            class Meta:
                apps = Apps()

        contact = FakeContact(
            pk=contact_id,  # contact_id won't define pk in subclass model; why?
            contact_id=contact_id,
            first_name='Test',
            middle_name='Ing',
            last_name='User',
            previous_name='',  # TODO
            phone_number='9165550100',
            mobile_number='9165550101',
            email='test.user@example.com',
            birth_date=date(1983, 10, 4),
            identification='000-123-4567',
            marital_status='married',
            co_applicant_first_name='CoTest',
            co_applicant_middle_name='CoIng',
            co_applicant_last_name='CoUser',
            co_applicant_previous_name='Co Previous Name',
            co_applicant_phone_number='9165550102',
            co_applicant_mobile_number='9165550103',
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
            work_phone='9165550104',
            co_applicant_employer='Co Testing Employer, Inc',
            co_applicant_employment_status='employed',
            co_applicant_position='Supervisor',
            co_applicant_length_of_employment='5 years',
            co_applicant_work_phone='9165550105',
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
            call_center_representative=self.request.user,
            last_status_change=today,
            created_at=today - timedelta(days=2),
            updated_at=today - timedelta(days=1),

            bank_account=bank_account,
            company=company,
            lead_source=lead_source,
            stage=stage,
            status=status,
        )

        return contact
