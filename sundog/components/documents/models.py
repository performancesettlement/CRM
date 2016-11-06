from datetime import date, timedelta
from django.contrib.auth.models import User
from django.db.models import (
    CASCADE,
    DateTimeField,
    ForeignKey,
    Model,
    SET_NULL,
)
from django.urls import reverse
from django_auth_app.enums import US_STATES
from multiselectfield import MultiSelectField
from pystache import render
from settings import MEDIA_PRIVATE
from sundog.media import S3PrivateFileField
from sundog.models import ACCOUNT_TYPE_CHOICES, Contact, NONE_CHOICE_LABEL
from sundog.utils import LongCharField, default
from tinymce.models import HTMLField
from weasyprint import HTML


default_contact = Contact(
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
        'I was involved in a major car accident and had to take 3 months off of'
        ' work'
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
    # assigned_to=ForeignKey(User, null=True, blank=True),              # TODO
    # call_center_representative=ForeignKey(User),                      # TODO
    # lead_source=ForeignKey(LeadSource),                               # TODO
    # company=ForeignKey(Company, null=True, blank=True),               # TODO
    # stage=ForeignKey(Stage, blank=True, null=True),                   # TODO
    # status=ForeignKey(Status, blank=True, null=True),                 # TODO
    last_status_change=date.today(),
    created_at=date.today() - timedelta(days=2),
    updated_at=date.today() - timedelta(days=1),
)


def contact_context(contact=default_contact):
    def d(f):
        default(f, '')

    return {
        # Contact identification:
        'ID': contact.pk,
        'CUSTOMERID': contact.pk,

        # Applicant information:
        'FIRSTNAME': contact.first_name,
        'LASTNAME': contact.last_name,
        'MIDDLENAME': contact.middle_name,
        'FULLNAME': "{first_name} {last_name}".format(
            first_name=contact.first_name or '',
            last_name=contact.last_name or '',
        ),
        'PHONE': contact.phone_number,
        'HOMEPHONE_AREA': d(lambda: contact.phone_number[0:2]),
        'HOMEPHONE_PRE': d(lambda: contact.phone_number[3:5]),
        'HOMEPHONE_SUFF': d(lambda: contact.phone_number[6:]),
        'PHONE2': contact.work_phone,
        'WORKPHONE_AREA': d(lambda: contact.work_phone[0:2]),
        'WORKPHONE_PRE': d(lambda: contact.work_phone[3:5]),
        'WORKPHONE_SUFF': d(lambda: contact.work_phone[6:]),
        'PHONE3': contact.mobile_number,
        'CELLPHONE_AREA': d(lambda: contact.mobile_number[0:2]),
        'CELLPHONE_PRE': d(lambda: contact.mobile_number[3:5]),
        'CELLPHONE_SUFF': d(lambda: contact.mobile_number[6:]),
        'EMAIL': contact.email,
        # 'FAX': ,  # TODO: Fax
        'ADDRESS': contact.address_1,
        'ADDRESS2': contact.address_2,
        'CITY': contact.city,
        'STATE': contact.state,
        'STATEFULL': contact.state and str(
            next(
                (
                    name
                    for code, name in US_STATES
                    if code == contact.state
                ),
                '',
            ),
        ),
        'ZIP': contact.zip_code,
        'FULLADDRESS': (
            "{address_1}, {address_2}, {city} {state} {zip_code}".format(
                address_1=contact.address_1 or '',
                address_2=contact.address_2 or '',
                city=contact.city or '',
                state=contact.state or '',
                zip_code=contact.zip_code or '',
            )
        ),
        'SSN': contact.identification,
        # 'ENCSSN': ,  # TODO: Contact's Encrypted Social Security Number
        'SSN1': d(lambda: contact.identification[0]),
        'SSN2': d(lambda: contact.identification[1]),
        'SSN3': d(lambda: contact.identification[2]),
        'SSN4': d(lambda: contact.identification[4]),
        'SSN5': d(lambda: contact.identification[5]),
        'SSN6': d(lambda: contact.identification[6]),
        'SSN7': d(lambda: contact.identification[8]),
        'SSN8': d(lambda: contact.identification[9]),
        'SSN9': d(lambda: contact.identification[10]),
        'DOB': str(contact.birth_date),

        # Co-applicant information:
        'COFIRSTNAME': contact.co_applicant_first_name,
        'COLASTNAME': contact.co_applicant_last_name,
        'COMIDDLENAME': contact.co_applicant_middle_name,
        'COFULLNAME': "{first_name} {last_name}".format(
            first_name=contact.co_applicant_first_name,
            last_name=contact.co_applicant_last_name,
        ),
        'COPHONE': contact.co_applicant_phone_number,
        'COHOMEPHONE_AREA': d(lambda: contact.co_applicant_phone_number[0:2]),
        'COHOMEPHONE_PRE': d(lambda: contact.co_applicant_phone_number[3:5]),
        'COHOMEPHONE_SUFF': d(lambda: contact.co_applicant_phone_number[6:]),
        'COPHONE2': contact.co_applicant_work_phone,
        'COWORKPHONE_AREA': d(lambda: contact.co_applicant_work_phone[0:2]),
        'COWORKPHONE_PRE': d(lambda: contact.co_applicant_work_phone[3:5]),
        'COWORKPHONE_SUFF': d(lambda: contact.co_applicant_work_phone[6:]),
        'COPHONE3': contact.co_applicant_mobile_number,
        'COCELLPHONE_AREA': d(lambda: contact.co_applicant_mobile_number[0:2]),
        'COCELLPHONE_PRE': d(lambda: contact.co_applicant_mobile_number[3:5]),
        'COCELLPHONE_SUFF': d(lambda: contact.co_applicant_mobile_number[6:]),
        'COEMAIL': contact.co_applicant_email,
        # 'COFAX': ,  # TODO: Fax
        'COADDRESS': contact.co_applicant_address_1,
        'COADDRESS2': contact.co_applicant_address_2,
        'COCITY': contact.co_applicant_city,
        'COSTATE': contact.co_applicant_state,
        'COSTATEFULL': contact.co_applicant_state and str(
            next(
                (
                    name
                    for code, name in US_STATES
                    if code == contact.co_applicant_state
                ),
                '',
            ),
        ),
        'COZIP': contact.co_applicant_zip_code,
        'COFULLADDRESS': (
            "{address_1}, {address_2}, {city} {state} {zip_code}".format(
                address_1=contact.co_applicant_address_1,
                address_2=contact.co_applicant_address_2,
                city=contact.co_applicant_city,
                state=contact.co_applicant_state,
                zip_code=contact.co_applicant_zip_code,
            )
        ),
        'COSSN': contact.co_applicant_identification,
        # 'COENCSSN': ,  # TODO: Contact's Encrypted Social Security Number
        'COSSN1': d(lambda: contact.co_applicant_identification[0]),
        'COSSN2': d(lambda: contact.co_applicant_identification[1]),
        'COSSN3': d(lambda: contact.co_applicant_identification[2]),
        'COSSN4': d(lambda: contact.co_applicant_identification[4]),
        'COSSN5': d(lambda: contact.co_applicant_identification[5]),
        'COSSN6': d(lambda: contact.co_applicant_identification[6]),
        'COSSN7': d(lambda: contact.co_applicant_identification[8]),
        'COSSN8': d(lambda: contact.co_applicant_identification[9]),
        'COSSN9': d(lambda: contact.co_applicant_identification[10]),
        'CODOB': str(contact.co_applicant_birth_date),

        # Bank account information:
        'NAMEONACCT': contact.bank_account.name_on_account,
        'BANKNAME': contact.bank_account.bank_name,
        'BANKADDRESS': contact.bank_account.address,
        'BANKCITY': contact.bank_account.city,
        'BANKSTATE': contact.bank_account.state,
        'BANKZIP': contact.bank_account.zip_code,
        'BANKPHONE': contact.bank_account.phone,
        'ACCTTYPE': contact.bank_account.account_type and str(
            next(
                (
                    name
                    for code, name in ACCOUNT_TYPE_CHOICES
                    if code == contact.bank_account.account_type
                ),
                '',
            ),
        ),
        'ACCOUNTNUM': contact.bank_account.account_number,
        'ROUTINGNUM': contact.bank_account.routing_number,
        # 'ACCOUNTNUM_ENC': contact.bank_account.account_number,  # TODO: Encrypted Account Number  # noqa
        # 'ROUTINGNUM_ENC': contact.bank_account.routing_number,  # TODO: Encrypted Routing Number  # noqa
    }


TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('1099c', '1099-C'),
    ('30_day_notice', '30 Day Notice (debt has moved)'),
    ('3rd_party_auth', '3rd Party Speaker Authorization'),
    ('ach_authorization', 'ACH Authorization'),
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


class Document(Model):

    TYPE_CHOICES = TYPE_CHOICES
    TYPE_CHOICES_DICT = TYPE_CHOICES_DICT
    STATE_CHOICES = STATE_CHOICES
    STATE_CHOICES_DICT = STATE_CHOICES_DICT

    title = LongCharField()
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(to=User, on_delete=SET_NULL, blank=True, null=True)
    type = LongCharField(choices=TYPE_CHOICES)

    # FIXME: Work around stupid arbitrary length limits with a very large stupid
    # arbitrary length limit.  A proper fix would require a modified form of the
    # MultiSelectField class based on LongCharField, which could be accomplished
    # easily by forking the django-multiselectfield project and having it depend
    # on a new small package holding the LongCharField definition.
    state = MultiSelectField(choices=STATE_CHOICES, max_length=2**20)

    template_body = HTMLField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'documents.edit',
            args=[
                self.id,
            ]
        )

    def render(
        self,
        context={},
        contact=default_contact,
    ):
        return HTML(
            string=render(
                template=self.template_body,
                context={
                    **contact_context(contact),
                    **context,
                },
            ),
        )


def generated_document_filename(instance, filename):
    return '{base}generated_documents/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.contact.contact_id,
        filename=filename,
    )


class GeneratedDocument(Model):
    contact = ForeignKey(
        to=Contact,
        on_delete=CASCADE,
        related_name='generated_documents',
    )
    title = LongCharField()
    content = S3PrivateFileField(upload_to=generated_document_filename)
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(
        to=User,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='generated_documents',
    )
    template = ForeignKey(
        to=Document,
        blank=True,
        null=True,
        on_delete=SET_NULL,
        related_name='generated_documents',
    )

    def get_absolute_url(self):
        return self.content.url
