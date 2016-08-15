import hashlib
import uuid
from colorfield.fields import ColorField
from colorful.fields import RGBColorField
from decimal import Decimal
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from multi_email_field.fields import MultiEmailField
import pytz
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from sundog.utils import document_directory_path, format_price, get_now
import logging
from sundog import constants
from datetime import datetime
from django_auth_app import enums

logger = logging.getLogger(__name__)


class FileStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    related_color = models.CharField(max_length=20, null=True, blank=True, choices=constants.COLOR_CHOICES)
    related_percent = models.PositiveSmallIntegerField(null=True, blank=True,
                                                       validators=[MinValueValidator(0),
                                                                   MaxValueValidator(100)])
    order = models.SmallIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        verbose_name = 'File Status'
        verbose_name_plural = 'File Status List'

    def get_permission_codename(self):
        return constants.STATUS_CODENAME_PREFIX + self.name.lower().replace(" ", "_")

    def get_permission_name(self):
        return 'Can use status %s' % self.name.title()

    def save(self, *args, **kwargs):
        if not self.name.isupper():
            self.name = self.name.upper().strip()
        super(FileStatus, self).save(*args, **kwargs)


class FileStatusHistory(models.Model):
    previous_file_status_color = models.CharField(max_length=20, null=True, blank=True)
    previous_file_status = models.CharField(max_length=100, null=True, blank=True)
    new_file_status = models.CharField(max_length=100)
    new_file_status_color = models.CharField(max_length=20, null=True, blank=True)
    modifier_user_full_name = models.CharField(max_length=100)
    modifier_user_username = models.CharField(max_length=30)
    impersonated_by = models.ForeignKey(User, null=True)
    modified_time = models.DateTimeField()

    def __str__(self):
        return 'File %d (from %s to %s)' % (self.history_file_id, self.previous_file_status,
                                            self.new_file_status)

    class Meta:
        verbose_name = 'File History'
        verbose_name_plural = 'File History List'

    def create_new_file_status_history(self, previous_status, current_status, user, impersonator_user=None):
        self.modifier_user_full_name = user.get_full_name()
        self.modifier_user_username = user.username
        self.impersonated_by = impersonator_user
        self.new_file_status = current_status
        self.new_file_status_color = current_status.related_color
        if previous_status is not None:
            self.previous_file_status = previous_status
            self.previous_file_status_color = previous_status.related_color
        self.modified_time = datetime.now()
        self.save()


class ClientType(models.Model):
    client_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        verbose_name = 'Client Type'
        verbose_name_plural = 'Client Type List'

    def save(self, *args, **kwargs):
        if not self.name.isupper():
            self.name = self.name.upper()
        super(ClientType, self).save(*args, **kwargs)


class LeadSource(models.Model):
    lead_source_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


DEBT_SETTLEMENT = 'debt_settlement'
STUDENT_LOANS = 'student_loans'

STAGE_TYPE_CHOICES = (
    (DEBT_SETTLEMENT, 'Debt Settlement'),
    (STUDENT_LOANS, 'Student Loans'),
)


class Stage(models.Model):
    type = models.CharField(max_length=100, choices=STAGE_TYPE_CHOICES, default='debt_settlement')
    stage_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    order = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    color = RGBColorField(default='#FFFFFF')
    stage = models.ForeignKey(Stage, related_name='statuses', blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


COMPANY_TYPE_CHOICES = (
    ('law_firm', 'Law Firm'),
    ('lead_vendor', 'Lead Vendor'),
    ('marketing_company', 'Marketing Company'),
    ('partner', 'Partner'),
    ('servicing_company', 'Servicing Company'),
)

TIMEZONE_CHOICES = (
    ('eastern', 'Eastern'),
    ('central', 'Central'),
    ('mountain', 'Mountain'),
    ('pacific', 'Pacific')
)

ACCOUNT_EXEC_CHOICES = (
    (None, '--Select--'),
    ('user_test', 'User, Test'),
)

THEME_CHOICES = (
    (None, '--Select--'),
    ('default', 'Default'),
    ('light', 'Light'),
    ('perf_sett', 'PerfSett'),
    ('red_black', 'Red/Black'),
    ('red_gray', 'Red/Gray'),
)


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    active = models.BooleanField(default=False)
    company_type = models.CharField(choices=COMPANY_TYPE_CHOICES, max_length=100, blank=True, null=True)
    parent_company = models.ForeignKey('self', null=True)
    name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    company_code = models.CharField(max_length=100, blank=True, null=True)
    ein = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    address_2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    zip = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    fax = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    domain = models.CharField(max_length=100, blank=True, null=True)
    timezone = models.CharField(choices=TIMEZONE_CHOICES, max_length=100, blank=True, null=True)
    account_exec = models.CharField(choices=ACCOUNT_EXEC_CHOICES, max_length=100, blank=True, null=True)
    theme = models.CharField(choices=THEME_CHOICES, max_length=100, blank=True, null=True)
    upload_logo = models.FileField(max_length=100, blank=True, null=True)
    userfield_1 = models.CharField(max_length=100, blank=True, null=True)
    userfield_2 = models.CharField(max_length=100, blank=True, null=True)
    userfield_3 = models.CharField(max_length=100, blank=True, null=True)
    docusign_api_acct = models.CharField(max_length=100, blank=True, null=True)
    docusign_api_user = models.CharField(max_length=100, blank=True, null=True)
    docusign_password = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


MARITAL_STATUS_CHOICES = (
    (None, '--Select--'),
    ('single', 'Single'),
    ('married', 'Married'),
    ('separated', 'Separated'),
    ('divorced', 'Divorced'),
)

RESIDENTIAL_STATUS_CHOICES = (
    (None, '--Select--'),
    ('renter', 'Renter'),
    ('home_owner', 'Homeowner'),
    ('lives_with_f', 'Lives with family/friends'),
)

EMPLOYMENT_STATUS_CHOICES = (
    (None, '--Select--'),
    ('employed', 'Employed'),
    ('unemployed', 'Unemployed'),
    ('disabled', 'Disabled'),
    ('retired', 'Retired'),
)

DEPENDANTS_CHOICES = (
    (None, '--Select--'),
    ('0', 'None'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8'),
    ('9', '9'),
    ('10', '10'),
)

HARDSHIPS_CHOICES = (
    (None, '--Select--'),
    ('divorce_or_separation', 'Divorce or Separation'),
    ('disability', 'Disability'),
    ('death_in_family', 'Death In Family'),
    ('child_expenses', 'Child Expenses'),
    ('loss_of_employment', 'Loss of Employment'),
    ('medical_expenses', 'Medical Expenses'),
    ('pay_cut', 'Pay Cut'),
    ('relocation_expenses', 'Relocation Expenses'),
    ('temporary_loss_of_work', 'Temporary Loss of Work'),
    ('other', 'Other'),
)

AUTHORIZATION_FORM_ON_FILE_CHOICES = (
    (None, '--Select--'),
    ('yes', 'Yes'),
)


class Contact(models.Model):
    contact_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, default="")
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, default="")
    previous_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    mobile_number = models.CharField(max_length=50, default="")
    email = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    identification = models.CharField(max_length=100, unique=True, blank=True, null=True)
    marital_status = models.CharField(max_length=100, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    co_applicant_first_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_middle_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_last_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_previous_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_phone_number = models.CharField(max_length=50, blank=True, null=True)
    co_applicant_mobile_number = models.CharField(max_length=50, blank=True, null=True)
    co_applicant_email = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_birth_date = models.DateField(blank=True, null=True)
    co_applicant_identification = models.CharField(max_length=100, unique=True, blank=True, null=True)
    co_applicant_marital_status = models.CharField(max_length=100, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    dependants = models.CharField(max_length=100, choices=DEPENDANTS_CHOICES, blank=True, null=True)

    address_1 = models.CharField(max_length=300, blank=True, null=True)
    address_2 = models.CharField(max_length=300, blank=True, null=True)
    city = models.CharField(max_length=60, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    residential_status = models.CharField(max_length=100, choices=RESIDENTIAL_STATUS_CHOICES, blank=True, null=True)
    co_applicant_address = models.CharField(max_length=300, blank=True, null=True)
    co_applicant_city = models.CharField(max_length=60, blank=True, null=True)
    co_applicant_state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    co_applicant_zip_code = models.CharField(max_length=12, blank=True, null=True)

    employer = models.CharField(max_length=100, blank=True, null=True)
    employment_status = models.CharField(max_length=100, choices=EMPLOYMENT_STATUS_CHOICES, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    length_of_employment = models.CharField(max_length=100, blank=True, null=True)
    work_phone = models.CharField(max_length=50, blank=True, null=True)
    co_applicant_employer = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_employment_status = models.CharField(max_length=100, choices=EMPLOYMENT_STATUS_CHOICES, blank=True, null=True)
    co_applicant_position = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_length_of_employment = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_work_phone = models.CharField(max_length=50, blank=True, null=True)

    hardships = models.CharField(max_length=100, choices=HARDSHIPS_CHOICES, blank=True, null=True)
    hardship_description = models.CharField(max_length=300, blank=True, null=True)

    special_note_1 = models.CharField(max_length=100, blank=True, null=True)
    special_note_2 = models.CharField(max_length=100, blank=True, null=True)
    special_note_3 = models.CharField(max_length=100, blank=True, null=True)
    special_note_4 = models.CharField(max_length=100, blank=True, null=True)
    ssn1 = models.CharField(max_length=100, blank=True, null=True)
    ssn2 = models.CharField(max_length=100, blank=True, null=True)

    third_party_speaker_full_name = models.CharField(max_length=100, blank=True, null=True)
    third_party_speaker_last_4_of_ssn = models.CharField(max_length=100, blank=True, null=True)
    authorization_form_on_file = models.CharField(
        max_length=100, choices=AUTHORIZATION_FORM_ON_FILE_CHOICES, blank=True, null=True)

    active = models.BooleanField(default=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='assigned_to')
    call_center_representative = models.ForeignKey(User, related_name='call_center_representative')
    lead_source = models.ForeignKey(LeadSource)
    company = models.ForeignKey(Company, null=True, blank=True)
    stage = models.ForeignKey(Stage, related_name='contact', blank=True, null=True)
    status = models.ForeignKey(Status, related_name='contact', blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        permissions = (
            ("import_clients", "Can import clients"),
        )

    def __init__(self, *args, **kwargs):
        super(Contact, self).__init__(*args, **kwargs)
        full_name = self.last_name if self.last_name.strip() else ""
        full_name += (", " if full_name and self.first_name else "") + \
                     (self.first_name if self.first_name.strip() else "")
        self.full_name = full_name
        for stage_type in STAGE_TYPE_CHOICES:
            if stage_type == STAGE_TYPE_CHOICES[0]:
                self.type = stage_type[1]
                break

    def __str__(self):
        return '%s' % self.first_name

    def get_time_in_status(self):
        time_in_status = 'N/A'
        if self.last_status_change:
            seconds = (get_now() - self.last_status_change).total_seconds()
            days, seconds = divmod(seconds, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            if days > 0:
                time_in_status = 'Days %d' % days
            elif hours > 0:
                time_in_status = 'Hours %d' % hours
            elif minutes > 0:
                time_in_status = 'Minutes %d' % minutes
            else:
                time_in_status = 'Seconds %d' % seconds
        return time_in_status

    def save(self, *args, **kwargs):
        if self.contact_id is not None:
            orig = Contact.objects.get(contact_id=self.contact_id)
            if orig.status != self.status:
                self.last_status_change = datetime.now()
        if self.identification:
            self.identification.strip()
            if not self.identification.isupper():
                self.identification = self.identification.upper()
        super(Contact, self).save(*args, **kwargs)


ACCOUNT_TYPE_CHOICES = (
    (None, '--Select--'),
    ('checking', 'Checking'),
    ('savings', 'Savings'),
)


class BankAccount(models.Model):
    bank_account_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='bank_account', blank=True, null=True)
    routing_number = models.CharField(max_length=20)
    account_number = models.CharField(max_length=128)
    account_number_salt = models.CharField(max_length=32)
    account_number_last_4_digits = models.CharField(max_length=4)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    name_on_account = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


ACTIVITY_TYPE_CHOICES = (
    ('general', 'General'),
    ('re_assign', 'Re-Assign'),
    ('bank', 'Bank'),
    ('enrollment', 'Enrollment'),
    ('calendar', 'Calendar'),
    ('payment', 'Payment'),
    ('status', 'Status'),
    ('docs', 'Docs'),
    ('debts', 'Debts'),
    ('budget', 'Savings'),
    ('call', 'Call'),
    ('note', 'Note'),
    ('email', 'Email'),
)


ACTIVITY_TYPE_COLOR = {
    'general': '#a09652',
    're_assign': '#e2aa00',
    'bank': '#69b980',
    'enrollment': '#ebd200',
    'calendar': '#a662c3',
    'payment': '#7b7b7b',
    'status': '#e25500',
    'docs': '#00a3df',
    'debts': '#135100',
    'budget': '#218000',
    'call': '#be0000',
    'note': '#ba5300',
    'email': '#63cec3',
}


class Activity(models.Model):
    activity_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='activities', blank=True, null=True)
    type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    description = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)

    def get_type(self):
        for activity_type in ACTIVITY_TYPE_CHOICES:
            if activity_type[0] == self.type:
                return activity_type[1]

    def get_color(self):
        return ACTIVITY_TYPE_COLOR[self.type]


CALL_TYPE_CHOICES = (
    ('outgoing', 'Outgoing'),
    ('incoming', 'Incoming'),
)

CALL_EVENT_TYPE_CHOICES = (
    (None, '--Select--'),
    ('ppr', 'PPR'),
    ('welcome_call', 'Welcome Call'),
)

CALL_RESULT_TYPE_CHOICES = (
    (None, '--Select--'),
    ('already_in_program', 'Already In Program'),
    ('busy', 'Busy'),
    ('connected', 'Connected'),
    ('disconnected', 'Disconnected'),
    ('do_not_contact', 'Do Not Contact'),
    ('hung_up', 'Hung Up'),
    ('left_message', 'Left Message'),
    ('no_answer', 'No Answer'),
    ('wrong_answer', 'Wrong Number'),
)


class Call(models.Model):
    call_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='calls', blank=True, null=True)
    type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    description = models.CharField(max_length=300, blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True, null=True)
    phone_from = models.CharField(max_length=10, blank=True, null=True)
    phone_to = models.CharField(max_length=10, blank=True, null=True)
    event_type = models.CharField(max_length=10, choices=CALL_EVENT_TYPE_CHOICES, blank=True, null=True)
    result = models.CharField(max_length=20, choices=CALL_RESULT_TYPE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)


@receiver(post_save, sender=Call)
def add_call_activity(sender, instance, **kwargs):
    activity = Activity(
        contact=instance.contact, type='call', description=instance.description, created_by=instance.created_by)
    activity.save()


EMAIL_TYPE_CHOICES = (
    ('manual', 'Manual'),
    ('automated', 'Automated'),
)


class Email(models.Model):
    email_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='emails', blank=True, null=True)
    message = models.CharField(max_length=10000, blank=True, null=True)
    type = models.CharField(max_length=10, choices=EMAIL_TYPE_CHOICES, blank=True, null=True)
    email_from = models.EmailField(max_length=300, blank=True, null=True)
    emails_to = models.CharField(max_length=300, blank=True, null=True)
    subject = models.CharField(max_length=1000, blank=True, null=True)
    cc = models.CharField(max_length=300, blank=True, null=True)
    attachment = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='sent_emails', blank=True, null=True)


NOTE_TYPE_CHOICES = (
    (None, '--Select--'),
    ('client_communication', 'Client Communication'),
    ('cancellation', 'Cancellation'),
    ('draft_change', 'Draft Change'),
    ('settlement_reached', 'Settlement Reached'),
    ('authorization_obtained', 'Authorization Obtained'),
    ('file_note', 'File Note'),
    ('negotiations', 'Negotiations'),
    ('settlement_complete', 'Settlement Complete'),
    ('nsf_attempt', 'NSF Attempt'),
    ('authorization_attempt', 'Authorization Attempt'),
    ('debt_change', 'Debt Change'),
    ('welcome_call_attempt', 'Welcome Call Attempt'),
    ('underwriting', 'Underwriting'),
    ('letter_mailed_to_client', 'Letter Mailed To Client'),
    ('settlement_processing', 'Settlement Processing'),
    ('harassment_protection_service', 'Harassment Protection Service'),
    ('welcome_call_complete', 'Welcome Call Complete'),
)


class Note(models.Model):
    note_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='notes', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES)
    cc = models.CharField(max_length=1000, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)


@receiver(post_save, sender=Note)
def add_note_activity(sender, instance, **kwargs):
    activity = Activity(
        contact=instance.contact, type='note', description=instance.description, created_by=instance.created_by)
    activity.save()


class Generated(models.Model):
    generated_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='generated_docs', blank=True, null=True)
    title = models.CharField(max_length=300)
    content = models.FileField(upload_to='/generated')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='generated_files', blank=True, null=True)


E_SIGNED_STATUS_CHOICES = (
    ('sent', 'Sent'),
    ('pending', 'Pending'),
    ('completed', 'completed'),
)


def e_signed_directory_path(instance, filename):
    return 'esigned/{0}/{1}'.format(instance.contact.contact_id, filename)


class ESigned(models.Model):
    e_signed_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='e_signed_docs', blank=True, null=True)
    title = models.CharField(max_length=300)
    content = models.FileField(upload_to=e_signed_directory_path)
    sender_ip = models.GenericIPAddressField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=E_SIGNED_STATUS_CHOICES, blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    sent_by = models.ForeignKey(User, related_name='e_signed_sent_files', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(ESigned, self).__init__(*args, **kwargs)
        for e_sign_status in E_SIGNED_STATUS_CHOICES:
            if e_sign_status[0] == self.e_sign_status:
                self.status_label = e_sign_status[1]
                break


class Signer(models.Model):
    e_signed = models.ForeignKey(ESigned, related_name='signers')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    opened_at = models.DateTimeField(blank=True, null=True)
    signed_at = models.DateTimeField(blank=True, null=True)
    signing_ip = models.GenericIPAddressField()


DOCUMENT_TYPE_CHOICES = (
    (None, '--Select--'),
    ('1099c', '1099-C'),
    ('30_day_notice', '30 Day Notice (debt has moved)'),
    ('3rd_party_auth', '3rd Party Speaker Authorization'),
    ('auth_to_comm_with_cred', 'Auth. To Communicate w/ Creditors'),
    ('client_correspondence', 'Client Correspondence'),
    ('collector_correspondence', 'Collector Correspondence'),
    ('contract_agreement', 'Contract / Agreement'),
    ('credit_report', 'Credit Report'),
    ('creditor_correspondence', 'Creditor Correspondence'),
    ('general', 'General / Misc.'),
    ('hardship_notification', 'Hardship Notification Letter'),
    ('hardship_statement', 'Hardship Statement'),
    ('inc_exp_form', 'Inc/Exp Form'),
    ('legal_document', 'Legal Document'),
    ('legal_solicitation', 'Legal Solicitation Notice'),
    ('quality_control_rec', 'Quality Control Recording'),
    ('settlement_letter', 'Settlement Letter'),
    ('settlement_offer', 'Settlement Offer'),
    ('settlement_payment_confirmation', 'Settlement Payment Confirmation'),
    ('settlement_recording', 'Settlement Recording'),
    ('statement', 'Statement'),
    ('summons', 'Summons'),
    ('term_checker', 'Term Checker'),
    ('unknown_creditor', 'Unknown Creditor'),
)


def uploaded_directory_path(instance, filename):
    return 'uploaded/{0}/{1}'.format(instance.contact.contact_id, filename)


class Uploaded(models.Model):
    uploaded_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='uploaded_docs', blank=True, null=True)
    name = models.CharField(max_length=300)
    description = models.CharField(max_length=2000)
    type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, blank=True, null=True)
    content = models.FileField(upload_to=uploaded_directory_path)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='uploaded_files', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Uploaded, self).__init__(*args, **kwargs)
        for document_type in DOCUMENT_TYPE_CHOICES:
            if document_type[0] == self.type:
                self.type_label = document_type[1]
                break

    
class Source(models.Model):
    source_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return '%s' % self.name


class DataSource(models.Model):
    data_source_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return '%s' % self.name


CAMPAIGN_PRIORITY_CHOICES = (
    (None, '--Select--'),
    (0, '0'),
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
    (8, '8'),
    (9, '9'),
    (10, '10'),
)

CAMPAIGN_SOURCES_CHOICES = (
    (None, '--Select--'),
    ('billboard', 'Billboard'),
    ('directmail', 'DirectMail'),
    ('email', 'Email'),
    ('internal_transfer', 'Internal Transfer'),
    ('internet', 'Internet'),
    ('other', 'Other'),
    ('radio', 'Radio'),
    ('television', 'Television'),
)


class Campaign(models.Model):
    campaign_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    active = models.BooleanField(default=True)
    title = models.CharField(max_length=100)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    source = models.ForeignKey(Source, blank=True, null=True)
    media_type = models.CharField(max_length=100, blank=True, null=True, choices=CAMPAIGN_SOURCES_CHOICES)
    priority = models.PositiveSmallIntegerField(null=True, blank=True, choices=CAMPAIGN_PRIORITY_CHOICES)
    cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    purchase_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return '%s' % self.title


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return '%s' % self.name

    def save(self, *args, **kwargs):
        if not self.name.isupper():
            self.name = self.name.upper()
        super(Tag, self).save(*args, **kwargs)


class Message(models.Model):
    message = models.CharField(max_length=255)
    user = models.ForeignKey(User)
    time = models.DateTimeField()

    def __str__(self):
        return '%s: %s' % (self.user.get_full_name(), self.message)


class MyFile(models.Model):
    file_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=1000)
    current_status = models.ForeignKey(FileStatus)
    client = models.ForeignKey(Contact)
    priority = models.PositiveSmallIntegerField(null=True, blank=True,
                                                choices=constants.PRIORITY_CHOICES)
    tags = models.ManyToManyField(Tag)
    quoted_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    quoted_date = models.DateField(null=True, blank=True)
    invoice_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    creator_user_full_name = models.CharField(max_length=100)
    creator_user_username = models.CharField(max_length=30)
    created_time = models.DateTimeField()
    active = models.BooleanField(default=True)
    last_update_user_full_name = models.CharField(max_length=100)
    last_update_user_username = models.CharField(max_length=30)
    last_update_time = models.DateTimeField()
    file_status_history = models.ManyToManyField(FileStatusHistory)
    messages = models.ManyToManyField(Message)
    participants = models.ManyToManyField(User)

    def __str__(self):
        return '%d - %s' % (self.file_id, self.description)

    class Meta:
        verbose_name = 'File'
        verbose_name_plural = 'Files'
        permissions = (
            ("view_all_files", "Can view all files"),
            ("import_files", "Can import files"),
            ("change_file_participant", "Can add/remove participants from a file"),
            ("change_file_tag", "Can add/remove tags from a file"),
        )

    def save(self, *args, **kwargs):
        if not self.description.isupper():
            self.description = self.description.upper()
        super(MyFile, self).save(*args, **kwargs)

    def get_permission_codename(self):
        return constants.FILE_CODENAME_PREFIX + str(self.file_id)

    def get_permission_name(self):
        return 'Can use file ' + self.__str__().upper()[0:70]

    def stamp_created_values(self, user):
        self.creator_user_username = user.username
        self.creator_user_full_name = user.get_full_name()
        self.created_time = datetime.now()
        self.stamp_updated_values(user)

    def stamp_updated_values(self, user):
        self.last_update_time = datetime.now()
        self.last_update_user_username = user.username
        self.last_update_user_full_name = user.get_full_name()

    def add_temp_tags(self, tag):
        if not hasattr(self, 'added_tags'):
            self.added_tags = []
        self.added_tags.append(tag)

    def get_temp_tags(self):
        if not hasattr(self, 'added_tags'):
            return []
        else:
            return self.added_tags

    def add_temp_users(self, username):
        if not hasattr(self, 'added_users'):
            self.added_users = []
        self.added_users.append(username)

    def get_temp_users(self):
        if not hasattr(self, 'added_users'):
            return []
        else:
            return self.added_users

    def get_participants_hashcode(self):
        participants = list(self.participants.all())
        hash_string = "participants_".join([str(participant.id) for participant in participants]) if participants else "participants"
        return hashlib.sha1(hash_string.encode('utf-8')).hexdigest()

    def get_hashcode(self):
        description = "desc_" + self.description if self.description else "desc"
        status_id = "status_" + str(self.current_status.status_id) if self.current_status else "status"
        client_id = "client_" + str(self.client.client_id) if self.client else "client"
        priority = "priority_" + str(self.priority) if self.priority else ""
        tags = list(self.tags.all())
        tags_id = "tags_    ".join([str(tag.id) for tag in tags]) if tags else "tags"
        quoted_price = "quoted_price_" + format_price(self.quoted_price) if self.quoted_price else "quoted_price"
        quoted_date = "quoted_date_" + str(self.quoted_date) if self.quoted_date else "quoted_date"
        invoice_price = "invoice_price_" + format_price(self.invoice_price) if self.invoice_price else "invoice_price"
        invoice_date = "invoice_date_" + str(self.invoice_date) if self.invoice_date else "invoice_date"

        hash_string = "__".join([status_id, description, client_id, priority, quoted_price, quoted_date, invoice_price,
                                invoice_date, tags_id])
        return hashlib.sha1(hash_string.encode('utf-8')).hexdigest()


class Document(models.Model):
    document = models.FileField(upload_to=document_directory_path)
    file = models.ForeignKey(MyFile)

    def __str__(self):
        return '%s' % self.document.path


class FileAccessHistory(models.Model):
    user = models.ForeignKey(User)
    file = models.ForeignKey(MyFile)
    time = models.DateTimeField()

    def __str__(self):
        return 'Access to file %d for the user %s on %s' % (self.file.file_id, self.user.username, self.time)


class FileImportHistory(models.Model):
    import_file_path = models.CharField(max_length=255)
    import_checksum = models.CharField(max_length=50)
    user_full_name = models.CharField(max_length=100)
    user_username = models.CharField(max_length=30)
    import_time = models.DateTimeField()
    impersonated_by = models.ForeignKey(User, null=True)

    def __str__(self):
        return 'Import file to %s by the user %s on %s' % (self.import_file_path, self.user_username, self.import_time)


class FileStatusStat(models.Model):
    date_stat = models.DateField()
    file_status = models.CharField(max_length=100)
    file_count = models.IntegerField()

    class Meta:
        unique_together = ('date_stat', 'file_status',)


# CMS PAGES #
class Terms(Page):
    subtitle = RichTextField(null=True)
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('body', classname="full"),
    ]
