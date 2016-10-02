import copy
import hashlib
from colorful.fields import RGBColorField
from decimal import Decimal
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from sundog.utils import format_price, get_now
import logging
from sundog import constants
from datetime import datetime
from django_auth_app import enums
from settings import MEDIA_PRIVATE
from sundog.media import S3PrivateFileField
from sundog.routing import package_models

import sundog.view
import sys


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
    type = models.CharField(max_length=15, choices=STAGE_TYPE_CHOICES, default=DEBT_SETTLEMENT)
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


class WorkflowSettings(models.Model):
    workflow_settings_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=15, choices=STAGE_TYPE_CHOICES, default='debt_settlement')
    require_plan = models.BooleanField(default=False)
    require_bank = models.BooleanField(default=False)
    require_credit_card = models.BooleanField(default=False)
    require_bank_or_cc = models.BooleanField(default=False)
    require_debts = models.BooleanField(default=False)
    require_submit = models.BooleanField(default=False)
    require_contract_to_submit = models.BooleanField(default=False)
    require_contract_to_enroll = models.BooleanField(default=False)
    allow_reject = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    require_secondary_approval = models.BooleanField(default=False)
    require_inc_exp = models.BooleanField(default=False)
    enforce_required_fields = models.BooleanField(default=False)
    require_comp_template = models.BooleanField(default=False)
    pause_on_nsf = models.BooleanField(default=False)
    on_submission = models.ForeignKey(Status, related_name='on_submission', blank=True, null=True)
    on_returned = models.ForeignKey(Status, related_name='on_returned', blank=True, null=True)
    on_reject = models.ForeignKey(Status, related_name='on_reject', blank=True, null=True)
    on_approval = models.ForeignKey(Status, related_name='on_approval', blank=True, null=True)
    on_second_approval = models.ForeignKey(Status, related_name='on_second_approval', blank=True, null=True)
    on_enrollment = models.ForeignKey(Status, related_name='on_enrollment', blank=True, null=True)
    on_de_enroll = models.ForeignKey(Status, related_name='on_de_enroll', blank=True, null=True)
    on_re_enroll = models.ForeignKey(Status, related_name='on_re_enroll', blank=True, null=True)
    on_graduation = models.ForeignKey(Status, related_name='on_graduation', blank=True, null=True)
    on_un_graduate = models.ForeignKey(Status, related_name='on_un_graduate', blank=True, null=True)
    on_dropped = models.ForeignKey(Status, related_name='on_dropped', blank=True, null=True)
    on_contract_upload = models.ForeignKey(Status, related_name='on_contract_upload', blank=True, null=True)
    on_first_payment_processed = models.ForeignKey(Status, related_name='on_first_payment_processed', blank=True, null=True)
    on_first_payment_cleared = models.ForeignKey(Status, related_name='on_first_payment_cleared', blank=True, null=True)
    on_first_payment_return = models.ForeignKey(Status, related_name='on_first_payment_return', blank=True, null=True)
    on_final_payment = models.ForeignKey(Status, related_name='on_final_payment', blank=True, null=True)
    on_pause = models.ForeignKey(Status, related_name='on_pause', blank=True, null=True)
    on_resume = models.ForeignKey(Status, related_name='on_resume', blank=True, null=True)
    on_returned_payment = models.ForeignKey(Status, related_name='on_returned_payment', blank=True, null=True)


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

NONE_CHOICE_LABEL = '--Select--'

ACCOUNT_EXEC_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('user_test', 'User, Test'),
)

THEME_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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
    address_2 = models.CharField(max_length=1000, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    zip = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    fax = models.CharField(max_length=10, blank=True, null=True)
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
    (None, NONE_CHOICE_LABEL),
    ('single', 'Single'),
    ('married', 'Married'),
    ('separated', 'Separated'),
    ('divorced', 'Divorced'),
)

RESIDENTIAL_STATUS_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('renter', 'Renter'),
    ('home_owner', 'Homeowner'),
    ('lives_with_f', 'Lives with family/friends'),
)

EMPLOYMENT_STATUS_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('employed', 'Employed'),
    ('unemployed', 'Unemployed'),
    ('disabled', 'Disabled'),
    ('retired', 'Retired'),
)

DEPENDANTS_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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
    (None, NONE_CHOICE_LABEL),
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
    (None, NONE_CHOICE_LABEL),
    ('yes', 'Yes'),
)


class Contact(models.Model):
    contact_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, default="")
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, default="")
    previous_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    mobile_number = models.CharField(max_length=50, default="")
    email = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    identification = models.CharField(max_length=100, unique=True, blank=True, null=True)
    marital_status = models.CharField(max_length=100, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    co_applicant_first_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_middle_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_last_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_previous_name = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_phone_number = models.CharField(max_length=10, blank=True, null=True)
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
    work_phone = models.CharField(max_length=10, blank=True, null=True)
    co_applicant_employer = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_employment_status = models.CharField(max_length=100, choices=EMPLOYMENT_STATUS_CHOICES, blank=True, null=True)
    co_applicant_position = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_length_of_employment = models.CharField(max_length=100, blank=True, null=True)
    co_applicant_work_phone = models.CharField(max_length=10, blank=True, null=True)

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
            ('import_clients', 'Can import clients'),
        )

    def __init__(self, *args, **kwargs):
        super(Contact, self).__init__(*args, **kwargs)
        full_name = self.last_name if self.last_name.strip() else ''
        full_name += (', ' if full_name and self.first_name else '') + \
                     (self.first_name if self.first_name.strip() else '')
        full_name_straight = (self.first_name if self.first_name.strip() else '')
        full_name_straight += (' ' if full_name and self.first_name else '') + \
                              (self.last_name if self.last_name.strip() else '')
        self.full_name = full_name
        self.full_name_straight = full_name_straight
        for stage_type in STAGE_TYPE_CHOICES:
            if stage_type == STAGE_TYPE_CHOICES[0]:
                self.type = stage_type[1]
                break

    def __str__(self):
        return '%s' % self.first_name

    def debts_count(self):
        return len(self.contact_debts.all())

    def total_enrolled_original_debts(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if debt.enrolled and debt.original_debt_amount:
                total += debt.original_debt_amount
        return total

    def total_enrolled_current_debts(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if debt.enrolled and debt.current_debt_amount:
                total += debt.current_debt_amount
        return total

    def total_not_enrolled_current_debts(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if not debt.enrolled and debt.current_debt_amount:
                total += debt.current_debt_amount
        return total

    def total_enrolled_current_payments(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if debt.enrolled and debt.current_payment:
                total += debt.current_payment
        return total

    def total_not_enrolled_current_payments(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if not debt.enrolled and debt.current_payment:
                total += debt.current_payment
        return total

    def total_settled(self):
        # TODO: implement logic
        return Decimal('0.00')

    def average_settled(self):
        # TODO: implement logic
        return Decimal('0.00')

    def highest_settled(self):
        # TODO: implement logic
        return Decimal('0.00')

    def lowest_settled(self):
        # TODO: implement logic
        return Decimal('0.00')

    def client_balance(self):
        # TODO: implement logic
        return Decimal('0.00')

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
        if self.identification == '':
            self.identification = None
        if self.co_applicant_identification == '':
            self.co_applicant_identification = None
        super(Contact, self).save(*args, **kwargs)


class FeeProfile(models.Model):
    fee_profile_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class FeeProfileRule(models.Model):
    fee_profile_rule_id = models.AutoField(primary_key=True)
    fee_profile = models.ForeignKey(FeeProfile, related_name='rules', blank=True, null=True)
    accts_low = models.DecimalField(max_digits=14, decimal_places=2)
    accts_high = models.DecimalField(max_digits=14, decimal_places=2)
    debt_low = models.DecimalField(max_digits=14, decimal_places=2)
    debt_high = models.DecimalField(max_digits=14, decimal_places=2)
    fixed_low = models.DecimalField(max_digits=14, decimal_places=2)
    fixed_high = models.DecimalField(max_digits=14, decimal_places=2)
    fixed_inc = models.DecimalField(max_digits=14, decimal_places=2)
    monthly_low = models.DecimalField(max_digits=14, decimal_places=2)
    monthly_high = models.DecimalField(max_digits=14, decimal_places=2)
    monthly_inc = models.DecimalField(max_digits=14, decimal_places=2)
    min_term = models.PositiveSmallIntegerField()
    max_term = models.PositiveSmallIntegerField()
    inc	= models.PositiveSmallIntegerField()
    sett_fee_low = models.DecimalField(max_digits=14, decimal_places=2)
    sett_fee_high = models.DecimalField(max_digits=14, decimal_places=2)
    sett_inc = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['fee_profile_rule_id']


MONTH_CHOICES = [(str(x), str(x) + ' Month') for x in range(1, 301)]

AMOUNT_CHOICES = [(0, '0.0%')] + [(str(x/2), str(x/2) + '%') for x in range(1, 102)]

WITH_AFTER_FEE_CHOICES = copy.copy(MONTH_CHOICES) + [('after_1', 'After Fee 1'), ('after_2', 'After Fee 2')]


class EnrollmentPlan(models.Model):
    enrollment_plan_id = models.AutoField(primary_key=True)
    active = models.NullBooleanField()
    file_type = models.CharField(max_length=15, choices=STAGE_TYPE_CHOICES)
    name = models.CharField(max_length=128)
    two_monthly_drafts = models.NullBooleanField()
    select_first_payment_date = models.NullBooleanField()
    program_length_default = models.CharField(max_length=10, choices=WITH_AFTER_FEE_CHOICES, blank=True, null=True)
    program_length_minimum = models.CharField(max_length=10, choices=WITH_AFTER_FEE_CHOICES, blank=True, null=True)
    program_length_maximum = models.CharField(max_length=10, choices=WITH_AFTER_FEE_CHOICES, blank=True, null=True)
    program_length_increment = models.PositiveSmallIntegerField(null=True, blank=True)
    est_settlement_perc = models.PositiveSmallIntegerField(null=True, blank=True)
    est_settlement_perc_minimum = models.PositiveSmallIntegerField(null=True, blank=True)
    est_settlement_perc_maximum = models.PositiveSmallIntegerField(null=True, blank=True)
    est_settlement_perc_increment = models.PositiveSmallIntegerField(null=True, blank=True)
    performance_plan = models.NullBooleanField()
    draft_fee_separate = models.NullBooleanField()
    includes_veritas_legal = models.NullBooleanField()
    legal_plan_flag = models.NullBooleanField()
    debt_amount_flag = models.NullBooleanField()
    debt_amount_from = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    debt_amount_to = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    debt_to_income_flag = models.NullBooleanField()
    debt_to_income_ratio_from = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    debt_to_income_ratio_to = models.PositiveSmallIntegerField(default=0, null=True, blank=True)
    states_flag = models.NullBooleanField()
    states = models.CharField(max_length=120, blank=True, null=True)
    fee_profile = models.ForeignKey(FeeProfile, related_name='enrollment_plans_linked', blank=True, null=True)
    show_fee_subtotal_column = models.NullBooleanField()
    exceed_notification = models.PositiveSmallIntegerField(null=True, blank=True)
    savings_start = models.CharField(max_length=10, choices=WITH_AFTER_FEE_CHOICES, blank=True, null=True)
    savings_end = models.CharField(max_length=10, choices=[('entire', 'Entire Program')] + WITH_AFTER_FEE_CHOICES, blank=True, null=True)
    savings_adjustment = models.NullBooleanField()
    show_savings_accumulation = models.NullBooleanField()


YES_NO_CHOICES = (
    ('yes', 'Yes'),
    ('no', 'No'),
)

FEE_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('percent', 'Debt Percent'),
    ('fixed', 'Fixed Amount'),
    ('savings', 'Sett Savings'),
    ('fixedamort', 'Fixed Amort'),
    ('perdebt', 'Per Debt'),
)

WITH_HALF_FULL_CHOICES = [('half', 'Half'), ('full', 'Full')] + copy.copy(MONTH_CHOICES)


class Fee(models.Model):
    fee_id = models.AutoField(primary_key=True)
    enrollment_plan = models.ForeignKey(EnrollmentPlan, related_name='fees')
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=128, choices=FEE_TYPE_CHOICES)
    amount = models.CharField(max_length=4, choices=AMOUNT_CHOICES, default='0')
    defer = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    starts = models.CharField(max_length=10, choices=WITH_AFTER_FEE_CHOICES)
    ends = models.CharField(max_length=10, choices=WITH_HALF_FULL_CHOICES)
    weighted_fee_perc = models.PositiveSmallIntegerField(null=True, blank=True)
    weighted_fee_in_first = models.CharField(max_length=3, choices=WITH_AFTER_FEE_CHOICES)
    paid_by_check = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')
    hide = models.CharField(max_length=3, choices=YES_NO_CHOICES, default='no')


class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    enrollment_plan = models.ForeignKey(EnrollmentPlan, related_name='enrollments_linked', blank=True, null=True)
    contact = models.ForeignKey(Contact, related_name='enrollments', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def next_payment(self):
        # TODO: implement logic.
        return None

    def payments_made(self):
        # TODO: implement logic.
        return 0

    def balance(self):
        # TODO: implement logic.
        return 0

ACCOUNT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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
    phone = models.CharField(max_length=10, blank=True, null=True)
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
    (None, NONE_CHOICE_LABEL),
    ('ppr', 'PPR'),
    ('welcome_call', 'Welcome Call'),
)

CALL_RESULT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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
    (None, NONE_CHOICE_LABEL),
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


def generated_content_filename(instance, filename):
    return '{base}generated/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.contact.contact_id,
        filename=filename,
    )

class Generated(models.Model):
    generated_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='generated_docs', blank=True, null=True)
    title = models.CharField(max_length=300)
    content = S3PrivateFileField(upload_to=generated_content_filename)

    mime_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='generated_files', blank=True, null=True)

    def get_absolute_url(self):
        return self.content.url



E_SIGNED_STATUS_CHOICES = (
    ('sent', 'Sent'),
    ('pending', 'Pending'),
    ('completed', 'completed'),
)


def esigned_content_filename(instance, filename):
    return '{base}esigned/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.contact.contact_id,
        filename=filename,
    )

class ESigned(models.Model):
    e_signed_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='e_signed_docs', blank=True, null=True)
    title = models.CharField(max_length=300)
    content = S3PrivateFileField(upload_to=esigned_content_filename)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
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

    def get_absolute_url(self):
        return self.content.url


class Signer(models.Model):
    signer_id = models.AutoField(primary_key=True)
    e_signed = models.ForeignKey(ESigned, related_name='signers')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    opened_at = models.DateTimeField(blank=True, null=True)
    signed_at = models.DateTimeField(blank=True, null=True)
    signing_ip = models.GenericIPAddressField()


UPLOADED_DOCUMENT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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


def uploaded_content_filename(instance, filename):
    return '{base}uploaded/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=instance.contact.contact_id,
        filename=filename,
    )

class Uploaded(models.Model):
    uploaded_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='uploaded_docs', blank=True, null=True)
    name = models.CharField(max_length=300)
    description = models.CharField(max_length=2000)
    type = models.CharField(max_length=50, choices=UPLOADED_DOCUMENT_TYPE_CHOICES, blank=True, null=True)
    content = S3PrivateFileField(upload_to=uploaded_content_filename)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='uploaded_files', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Uploaded, self).__init__(*args, **kwargs)
        for document_type in UPLOADED_DOCUMENT_TYPE_CHOICES:
            if document_type[0] == self.type:
                self.type_label = document_type[1]
                break

    def get_type(self):
        split_name = self.name.split('.')
        if len(split_name) > 1:
            return split_name[-1]
        return ''

    def get_absolute_url(self):
        return self.content.url


class Incomes(models.Model):
    incomes_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='incomes', blank=True, null=True)
    take_home_pay = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    other_income = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    alimony = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    child_support = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    social_security = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    retirement_income = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    checking_account = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    checking_account_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    savings_account = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    savings_account_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    cash = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    cash_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    property_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    property_balance_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    stocks = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    stocks_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    vehicles = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    vehicles_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    other_incomes = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    other_incomes_lien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    def total(self):
        attrs = [
            'take_home_pay',
            'other_income',
            'alimony',
            'child_support',
            'social_security',
            'retirement_income',
            'checking_account',
            'checking_account_lien',
            'savings_account',
            'savings_account_lien',
            'cash',
            'cash_lien',
            'property_balance',
            'property_balance_lien',
            'stocks',
            'stocks_lien',
            'vehicles',
            'vehicles_lien',
            'other_incomes',
            'other_incomes_lien',
        ]
        total = Decimal('0.00')
        for attr in attrs:
            total += getattr(self, attr)
        return total

    def assets(self):
        attrs = [
            'checking_account',
            'checking_account_lien',
            'savings_account',
            'savings_account_lien',
            'cash',
            'cash_lien',
            'property_balance',
            'property_balance_lien',
            'stocks',
            'stocks_lien',
            'vehicles',
            'vehicles_lien',
            'other_incomes',
            'other_incomes_lien',
        ]
        total = Decimal('0.00')
        for attr in attrs:
            total += getattr(self, attr)
        return total


class Expenses(models.Model):
    expenses_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='expenses', blank=True, null=True)
    rent = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    utilities = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    transportation = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    insurance_premiums = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    food = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    telephone = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    medical_bills = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    back_taxes = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    student_loans = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    child_support = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    child_care = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    other_expenses = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    rent_2 = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    auto_other = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tv = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    charity = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    clothing = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    education = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    entertainment = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    health = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    home_insurance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    household_items = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    life_insurance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    laundry = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    medical_care = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    def total(self):
        attrs = [
            'rent',
            'utilities',
            'transportation',
            'insurance_premiums',
            'food',
            'telephone',
            'medical_bills',
            'back_taxes',
            'student_loans',
            'child_support',
            'child_care',
            'other_expenses',
            'rent_2',
            'auto_other',
            'tv',
            'charity',
            'clothing',
            'education',
            'entertainment',
            'health',
            'home_insurance',
            'household_items',
            'life_insurance',
            'laundry',
            'medical_care',
        ]
        total = Decimal('0.00')
        for attr in attrs:
            total += getattr(self, attr)
        return total


class Creditor(models.Model):
    creditor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    address_1 = models.CharField(max_length=1000, blank=True, null=True)
    address_2 = models.CharField(max_length=1000, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    zip_code = models.CharField(max_length=100, blank=True, null=True)
    phone_1 = models.CharField(max_length=10, blank=True, null=True)
    phone_2 = models.CharField(max_length=10, blank=True, null=True)
    fax = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return '%s' % self.name

    def total_debts(self):
        total_debts = Decimal('0.00')
        all_debts = list(self.creditor_debts.all()) + list(self.bought_debts.all())
        for debt in all_debts:
            if (not debt.debt_buyer or (debt.debt_buyer and debt.debt_buyer.creditor_id == self.creditor_id)) and debt.current_debt_amount:
                total_debts += debt.current_debt_amount
        return total_debts

    def total_debtors(self):
        all_debts = list(self.creditor_debts.all()) + list(self.bought_debts.all())
        count = len(all_debts)
        for debt in all_debts:
            if debt.debt_buyer and debt.debt_buyer.creditor_id != self.creditor_id:
                count -= 1
        return count

    def avg_settled(self):
        avg = Decimal('0.00')
        all_owed_money = Decimal('0.00')
        all_settled_money = Decimal('0.00')
        all_debts = list(self.creditor_debts.all()) + list(self.bought_debts.all())
        # TODO: check rule for settled amount!
        for debt in all_debts:
            if not debt.debt_buyer or (debt.debt_buyer and debt.debt_buyer.creditor_id == self.creditor_id):
                if debt.original_debt_amount:
                    all_owed_money += debt.original_debt_amount
                    all_settled_money += debt.original_debt_amount - debt.current_debt_amount
        if all_owed_money and all_settled_money:
            avg = (all_settled_money * Decimal('100')) / all_owed_money
        return format_price(avg)


DEBT_ACCOUNT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('difficult_creditor', 'Difficult Creditor'),
    ('payday_loan', 'Payday Loan'),
    ('standard', 'Standard'),
)

WHOSE_DEBT_CHOICES = (
    ('applicant', 'Applicant'),
    ('co_applicant', 'Co-Applicant'),
    ('joint', 'Joint'),
)


HAS_SUMMONS_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('yes', 'Yes'),
    ('no', 'No'),
)


class Debt(models.Model):
    debt_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='contact_debts', blank=True, null=True)
    original_creditor = models.ForeignKey(Creditor, related_name='creditor_debts', blank=True, null=True)
    original_creditor_account_number = models.CharField(max_length=32)
    debt_buyer = models.ForeignKey(Creditor, related_name='bought_debts', blank=True, null=True)
    debt_buyer_account_number = models.CharField(max_length=32, blank=True, null=True)
    account_type = models.CharField(max_length=20, choices=DEBT_ACCOUNT_TYPE_CHOICES, blank=True, null=True)
    original_debt_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    current_debt_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    current_payment = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    whose_debt = models.CharField(max_length=20, choices=WHOSE_DEBT_CHOICES, blank=True, null=True)
    last_payment_date = models.DateTimeField(blank=True, null=True)
    has_summons = models.CharField(max_length=20, choices=HAS_SUMMONS_TYPE_CHOICES, blank=True, null=True)
    summons_date = models.DateTimeField(blank=True, null=True)
    court_date = models.DateTimeField(blank=True, null=True)
    discovery_date = models.DateTimeField(blank=True, null=True)
    answer_date = models.DateTimeField(blank=True, null=True)
    service_date = models.DateTimeField(blank=True, null=True)
    paperwork_received_date = models.DateTimeField(blank=True, null=True)
    poa_sent_date = models.DateTimeField(blank=True, null=True)
    enrolled = models.NullBooleanField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Debt, self).__init__(*args, **kwargs)
        if self.account_type:
            for choice in DEBT_ACCOUNT_TYPE_CHOICES:
                if choice[0] == self.account_type:
                    self.account_type_label = choice[1]
                    break
        else:
            self.account_type_label = self.account_type
        if self.whose_debt:
            for choice in WHOSE_DEBT_CHOICES:
                if choice[0] == self.whose_debt:
                    self.whose_debt_label = choice[1]
                    break
        else:
            self.whose_debt_label = self.whose_debt
        if self.has_summons:
            for choice in HAS_SUMMONS_TYPE_CHOICES:
                if choice[0] == self.has_summons:
                    self.has_summons_label = choice[1]
                    break
        else:
            self.has_summons_label = self.has_summons

    def notes_count(self):
        return len(self.notes.all())

    def save(self, *args, **kwargs):
        if self.enrolled is None:
            self.enrolled = True if self.original_debt_amount and self.original_debt_amount >= Decimal('500') else False
        super(Debt, self).save(*args, **kwargs)


class DebtNote(models.Model):
    debt_note_id = models.AutoField(primary_key=True)
    debt = models.ForeignKey(Debt, related_name='notes', blank=True, null=True)
    content = models.CharField(max_length=2000, blank=True, null=True)


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
    (None, NONE_CHOICE_LABEL),
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
    (None, NONE_CHOICE_LABEL),
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


def sundogdocument_document_filename(instance, filename):
    return '{base}sundogdocument/{identifier}/{filename}'.format(
        base=MEDIA_PRIVATE,
        identifier=str(instance.file.file_id),
        filename=filename,
    )

class SundogDocument(models.Model):
    document = S3PrivateFileField(upload_to=sundogdocument_document_filename)
    file = models.ForeignKey(MyFile)

    def get_absolute_url(self):
        return self.document.url

    def __str__(self):
        return '%s' % self.document.url


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


for model in package_models(sundog.view):
    setattr(sys.modules[__name__], model.__name__, model)
