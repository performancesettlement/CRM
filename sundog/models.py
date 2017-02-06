from colorful.fields import RGBColorField
from decimal import Decimal
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.timezone import now
from localflavor.us.us_states import US_STATES
from numpy import arange
from settings import MEDIA_PRIVATE
from simple_history.models import HistoricalRecords
from sundog.constants import SHORT_DATE_FORMAT, CONTACT_DEFAULT_STAGE, CONTACT_DEFAULT_STATUS
from sundog.media import S3PrivateFileField
from sundog.routing import package_models
from sundog.templatetags.my_filters import currency
from sundog.util.models import LongCharField
from sundog.utils import format_price

import copy
import logging
import sundog.components
import sys


logger = logging.getLogger(__name__)


class TrackedAbstractBase(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class LeadSource(TrackedAbstractBase):
    lead_source_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


COMPANY_TYPE_CHOICES = (
    ('law_firm', 'Law Firm'),
    ('lead_vendor', 'Lead Vendor'),
    ('marketing_company', 'Marketing Company'),
    ('partner', 'Partner'),
    ('servicing_company', 'Servicing Company'),
)

NONE_CHOICE_LABEL = '--Select--'

ACCOUNT_EXEC_CHOICES = (
    ('', NONE_CHOICE_LABEL),
    ('user_test', 'User, Test'),
)

THEME_CHOICES = (
    ('', NONE_CHOICE_LABEL),
    ('default', 'Default'),
    ('light', 'Light'),
    ('perf_sett', 'PerfSett'),
    ('red_black', 'Red/Black'),
    ('red_gray', 'Red/Gray'),
)


class Company(TrackedAbstractBase):
    company_id = models.AutoField(primary_key=True)
    active = models.BooleanField(default=False)
    type = models.CharField(choices=COMPANY_TYPE_CHOICES, max_length=100, blank=True, null=True)
    parent_company = models.ForeignKey('self', related_name='children', blank=True, null=True)
    name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    company_code = models.CharField(max_length=100, blank=True, null=True)
    ein = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    address_2 = models.CharField(max_length=1000, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
    zip = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    domain = models.CharField(max_length=100, blank=True, null=True)
    account_exec = models.CharField(choices=ACCOUNT_EXEC_CHOICES, max_length=100, blank=True, null=True)
    userfield_1 = models.CharField(max_length=100, blank=True, null=True)
    userfield_2 = models.CharField(max_length=100, blank=True, null=True)
    userfield_3 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Company, self).__init__(*args, **kwargs)
        for type_choice in COMPANY_TYPE_CHOICES:
            if type_choice[0] == self.type:
                self.type_label = type_choice[1]
                break

    def get_enrolled(self):
        return self.contacts.exclude(enrollments__isnull=True)


class Team(TrackedAbstractBase):
    team_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    companies = models.ManyToManyField(Company, related_name='company_teams', blank=True)
    users = models.ManyToManyField(User, related_name='user_teams', blank=True)
    roles = models.ManyToManyField(Group, related_name='group_teams', blank=True)

    def __str__(self):
        return self.name


DEBT_SETTLEMENT = 'debt_settlement'
STUDENT_LOANS = 'student_loans'

STAGE_TYPE_CHOICES = (
    (DEBT_SETTLEMENT, 'Debt Settlement'),
    (STUDENT_LOANS, 'Student Loans'),
)


class Stage(TrackedAbstractBase):
    type = models.CharField(max_length=15, choices=STAGE_TYPE_CHOICES, default=DEBT_SETTLEMENT)
    stage_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    order = models.IntegerField(blank=True, null=True)
    teams = models.ManyToManyField(Team, related_name='stages_associated', blank=True)
    shared_with_all = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Status(TrackedAbstractBase):
    status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    color = RGBColorField(default='#FFFFFF')
    stage = models.ForeignKey(Stage, related_name='statuses', blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    teams = models.ManyToManyField(Team, related_name='statuses_associated', blank=True)
    shared_with_all = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class WorkflowSettings(TrackedAbstractBase):
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


class Contact(TrackedAbstractBase):
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
    state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    residential_status = models.CharField(max_length=100, choices=RESIDENTIAL_STATUS_CHOICES, blank=True, null=True)
    co_applicant_address_1 = models.CharField(max_length=300, blank=True, null=True)
    co_applicant_address_2 = models.CharField(max_length=300, blank=True, null=True)
    co_applicant_city = models.CharField(max_length=60, blank=True, null=True)
    co_applicant_state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
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

    public = models.BooleanField(default=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='assigned_to')
    call_center_representative = models.ForeignKey(User, related_name='call_center_representative', blank=True, null=True)
    lead_source = models.ForeignKey(LeadSource, blank=True, null=True)
    company = models.ForeignKey(Company, related_name='contacts', null=True, blank=True)
    stage = models.ForeignKey(Stage, related_name='contact', blank=True, null=True)
    status = models.ForeignKey(Status, related_name='contact', blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='contact_created', blank=True, null=True)

    for field in '''
        marketing_company
        servicing_company
        law_firm
        lead_vendor
        partner
    '''.split():
        vars()[field] = models.ForeignKey(
            to=Company,
            related_name=field + '_contacts',
            blank=True,
            null=True,
        )
    del field

    for field in '''
        negotiator
        sales_manager
        client_services_representative
        sales
        processor
        sales_lns
        supervisor
        attorney
        lendstreet
        manager
        abe
    '''.split():
        vars()[field] = models.ForeignKey(
            to=User,
            related_name=field + '_contacts',
            blank=True,
            null=True,
        )
    del field

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        permissions = (
            ('import_clients', 'Can import clients'),
        )
        get_latest_by = 'created_at'

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
        return self.full_name

    def get_bank_account(self):
        try:
            return self.bank_account
        except:
            return None

    def get_absolute_url(self):
        return reverse(
            viewname='contact_dashboard',
            kwargs={
                'contact_id': self.pk,
            },
        )

    def available_monthly(self):
        incomes = list(self.incomes.all())
        if incomes:
            incomes = incomes[0].total()
        else:
            incomes = Decimal('0.00')
        expenses = list(self.expenses.all())
        if expenses:
            expenses = expenses[0].total()
        else:
            expenses = Decimal('0.00')
        return incomes - expenses

    def est_sett(self, ids=None):
        est_sett = Decimal('0.00')
        debts = list(self.contact_debts.all())
        for debt in debts:
            if (not ids and debt.enrolled) or (ids and debt.debt_id in ids):
                est_sett += debt.get_est_sett()
        return est_sett

    def debts_count(self):
        return len(self.contact_debts.all())

    def total_enrolled_original_debts(self):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if debt.enrolled and debt.original_debt_amount:
                total += debt.original_debt_amount
        return total

    def total_enrolled_current_debts(self, ids=None):
        total = Decimal('0.00')
        for debt in list(self.contact_debts.all()):
            if (not ids and debt.enrolled and debt.current_debt_amount) or (ids and debt.debt_id in ids):
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
            seconds = (now() - self.last_status_change).total_seconds()
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
                self.last_status_change = now()
        if self.identification == '':
            self.identification = None
        if self.co_applicant_identification == '':
            self.co_applicant_identification = None
        super(Contact, self).save(*args, **kwargs)


CONTACT_PERMISSION_FORMAT = 'access_contact_{id}'


@receiver(post_save, sender=Contact)
def add_contact_permission(sender, instance, created, **kwargs):
    if created:
        permission = Permission(name='Can access contact id={id}'.format(id=instance.contact_id),
                                codename=CONTACT_PERMISSION_FORMAT.format(id=instance.contact_id),
                                content_type=ContentType.objects.get_for_model(instance))
        permission.save()
        if instance.created_by:
            instance.created_by.user_permissions.add(permission)


@receiver(post_save, sender=Contact)
def set_contact_default_stage_status(sender, instance, created, **kwargs):
    if created:
        instance.stage = instance.stage or Stage.objects.get(name=CONTACT_DEFAULT_STAGE)
        instance.status = instance.status or Status.objects.get(name=CONTACT_DEFAULT_STATUS)
        instance.save()


class FeeProfile(TrackedAbstractBase):
    fee_profile_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class FeeProfileRule(TrackedAbstractBase):
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
    inc = models.PositiveSmallIntegerField()
    sett_fee_low = models.DecimalField(max_digits=14, decimal_places=2)
    sett_fee_high = models.DecimalField(max_digits=14, decimal_places=2)
    sett_fee_inc = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['fee_profile_rule_id']


MONTH_CHOICES = [(str(x), str(x) + ' Month') for x in range(1, 301)]

AMOUNT_CHOICES = [(x, '{}%'.format(x)) for x in arange(Decimal('0.00'), Decimal('51.00'), Decimal('0.5'))]


class EnrollmentPlan(TrackedAbstractBase):
    enrollment_plan_id = models.AutoField(primary_key=True)
    active = models.NullBooleanField()
    file_type = models.CharField(max_length=15, choices=STAGE_TYPE_CHOICES)
    name = models.CharField(max_length=128)
    two_monthly_drafts = models.NullBooleanField()
    select_first_payment = models.NullBooleanField()
    program_length_default = models.CharField(max_length=10, choices=MONTH_CHOICES, blank=True, null=True)
    program_length_minimum = models.CharField(max_length=10, choices=MONTH_CHOICES, blank=True, null=True)
    program_length_maximum = models.CharField(max_length=10, choices=MONTH_CHOICES, blank=True, null=True)
    program_length_increment = models.PositiveSmallIntegerField(null=True, blank=True)
    debt_amount_flag = models.NullBooleanField()
    debt_amount_from = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    debt_amount_to = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    fee_profile = models.ForeignKey(FeeProfile, related_name='enrollment_plans_linked', blank=True, null=True)
    show_fee_subtotal_column = models.NullBooleanField()
    exceed_notification = models.PositiveSmallIntegerField(null=True, blank=True)
    savings_start = models.CharField(max_length=10, choices=MONTH_CHOICES, blank=True, null=True)
    savings_end = models.CharField(max_length=10, choices=[('entire', 'Entire Program')] + MONTH_CHOICES, blank=True, null=True)
    savings_adjustment = models.NullBooleanField()
    show_savings_accumulation = models.NullBooleanField()

    def __str__(self):
        return self.name


YES_NO_CHOICES = (
    (None, NONE_CHOICE_LABEL),
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


class FeePlan(TrackedAbstractBase):
    fee_plan_id = models.AutoField(primary_key=True)
    enrollment_plan = models.ForeignKey(EnrollmentPlan, related_name='fee_plans')
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=128, choices=FEE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    defer = models.CharField(max_length=3, null=True)
    discount = models.DecimalField(max_digits=14, decimal_places=2, null=True)

ACCOUNT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('checking', 'Checking'),
    ('savings', 'Savings'),
)


class Payee(TrackedAbstractBase):
    payee_id = models.AutoField(primary_key=True)
    default_for_company = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    routing_number = models.CharField(max_length=20)
    account_number = models.CharField(max_length=30)
    account_type = models.CharField(max_length=8, choices=ACCOUNT_TYPE_CHOICES)
    name_on_account = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    company = models.ForeignKey(Company, related_name='payees', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Payee, self).__init__(*args, **kwargs)
        self.str = str(self.payee_id) + '-' + self.name + ' ***' + self.account_number[-4:]
        for type_choice in ACCOUNT_TYPE_CHOICES:
            if type_choice[0] == self.account_type:
                self.account_type_label = type_choice[1]
                break

    def __str__(self):
        return self.str

    def get_all_payments(self):
        return list(self.payments_received.all())

    def get_all_cleared_payments(self):
        return list(self.payments_received.filter(cleared_date__isnull=False))


COMPENSATION_TEMPLATE_TYPES_CHOICES = (
    ('flat', 'Flat Amoritization'),
    ('variable', 'Variable Amortization'),
    ('formula', 'Formula Based'),
)

AVAILABLE_FOR_CHOICES = (
    ('this_company', 'This Company'),
    ('all_companies', 'All Companies'),
)


class CompensationTemplate(TrackedAbstractBase):
    compensation_template_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=COMPENSATION_TEMPLATE_TYPES_CHOICES)
    available_for = models.CharField(max_length=20, choices=AVAILABLE_FOR_CHOICES)

    def __str__(self):
        return self.name


COMPENSATION_TEMPLATE_PAYEE_TYPE_CHOICES = (
    ('credit', 'Credit'),
    ('transfer', 'Transfer'),
    ('transfer_credit', 'Transfer Credit'),
)


class CompensationTemplatePayee(TrackedAbstractBase):
    compensation_template_payee_id = models.AutoField(primary_key=True)
    compensation_template = models.ForeignKey(CompensationTemplate, related_name='payees')
    type = models.CharField(max_length=20, choices=COMPENSATION_TEMPLATE_PAYEE_TYPE_CHOICES)
    fee_amount = models.DecimalField(max_digits=5, decimal_places=2, validators=[MaxValueValidator(Decimal('100.00')),
                                                                                 MinValueValidator(Decimal('0.01'))])
    payee = models.ForeignKey(Payee, related_name='compensation_template_payees')


CUSTODIAL_ACCOUNT_CHOICES = [('epps', 'EPPS'), ('dpg', 'DPG Custodial')]


class Enrollment(TrackedAbstractBase):
    enrollment_id = models.AutoField(primary_key=True)
    enrollment_plan = models.ForeignKey(EnrollmentPlan, related_name='enrollments_linked', blank=True, null=True)
    contact = models.ForeignKey(Contact, related_name='enrollments', blank=True, null=True)
    custodial_account = models.CharField(max_length=4, choices=CUSTODIAL_ACCOUNT_CHOICES, default='epps')
    compensation_template = models.ForeignKey(CompensationTemplate, blank=True, null=True)
    program_length = models.CharField(max_length=4)
    start_date = models.DateTimeField()
    first_date = models.DateTimeField()
    second_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'

    def __init__(self, *args, **kwargs):
        super(Enrollment, self).__init__(*args, **kwargs)
        for custodial_choice in CUSTODIAL_ACCOUNT_CHOICES:
            if custodial_choice[0] == self.custodial_account:
                self.custodial_account_label = custodial_choice[1]
                break

    def next_payment(self):
        date = None
        date_now = now()
        for payment in list(self.payments.all()):
            if date_now < payment.date:
                date = payment.date
                break
        return date

    def payments_made(self):
        payments_count = 0
        for payment in list(self.payments.all()):
            if payment.charge_type == 'payment' and payment.status == 'cleared':
                payments_count += 1
        return payments_count

    def payments_count(self):
        count = 0
        for payment in list(self.payments.all()):
            if payment.charge_type == 'payment':
                count += 1
        return count

    def total_payment(self):
        total = Decimal('0.00')
        for payment in list(self.payments.all()):
                total += payment.amount
        return total

    def fees_made(self):
        payments_count = 0
        for payment in list(self.payments.all()):
            if payment.charge_type == 'fee' and payment.status == 'cleared':
                payments_count += 1
        return payments_count

    def fees_count(self):
        count = 0
        for payment in list(self.payments.all()):
            if payment.charge_type == 'fee':
                count += 1
        return count

    def balance(self):
        # TODO: implement logic.
        return Decimal('0.00')


class Fee(TrackedAbstractBase):
    fee_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    fee_plan = models.ForeignKey(FeePlan, related_name='fees_related', blank=True, null=True)
    type = models.CharField(max_length=128, choices=FEE_TYPE_CHOICES)
    enrollment = models.ForeignKey(Enrollment, related_name='fees', blank=True, null=True)


class Creditor(TrackedAbstractBase):
    creditor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    address_1 = models.CharField(max_length=1000, blank=True, null=True)
    address_2 = models.CharField(max_length=1000, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
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

DEBT_ACCOUNT_EST_SETT = {
    'difficult_creditor': Decimal('65'),
    'payday_loan': Decimal('40'),
    'standard': Decimal('40'),
}

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


class Debt(TrackedAbstractBase):
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

    def get_settlement_offer(self):
        return self.offers.all().first()

    def get_est_sett(self):
        return self.current_debt_amount * (DEBT_ACCOUNT_EST_SETT.get(self.account_type, Decimal('40')) / 100)

    def notes_count(self):
        return len(self.notes.all())

    def owed_to(self):
        return self.debt_buyer if self.debt_buyer else self.original_creditor

    def debt_text(self):
        return self.original_creditor.name + ': ' + currency(self.current_debt_amount)

    def save(self, *args, **kwargs):
        if self.enrolled is None:
            self.enrolled = True if self.original_debt_amount and self.original_debt_amount >= Decimal('500') else False
        super(Debt, self).save(*args, **kwargs)


SETTLEMENT_OFFER_MADE_BY_CHOICES = (
    ('negotiator', 'Negotiator'),
    ('client', 'Client'),
)

SETTLEMENT_OFFER_STATUS_CHOICES = (
    ('in_review', 'In-Review'),
    ('declined', 'Declined'),
    ('accepted', 'Accepted'),
    ('completed', 'Completed'),
    ('client_auth_needed', 'Client Authorization is Needed'),
    ('sett_letter_needed', 'Settlement Letter is Needed'),
    ('client_auth_sett_letter_needed', 'Client Authorization and Settlement Letter are Needed'),
)


class SettlementOffer(TrackedAbstractBase):
    settlement_offer_id = models.AutoField(primary_key=True)
    enrollment = models.ForeignKey(Enrollment, related_name='settlement_offers')
    debt = models.ForeignKey(Debt, related_name='offers')
    made_by = models.CharField(max_length=10, choices=SETTLEMENT_OFFER_MADE_BY_CHOICES, default='negotiator')
    negotiator = models.ForeignKey(User, related_name='negotiated_offers')
    status = models.CharField(max_length=40, choices=SETTLEMENT_OFFER_STATUS_CHOICES,  default='in_review')
    date = models.DateTimeField()
    valid_until = models.DateTimeField(blank=True, null=True)
    debt_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    offer_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    notes = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(SettlementOffer, self).__init__(*args, **kwargs)
        if self.made_by:
            for choice in SETTLEMENT_OFFER_MADE_BY_CHOICES:
                if choice[0] == self.made_by:
                    self.made_by_label = choice[1]
                    break
        if self.status:
            for choice in SETTLEMENT_OFFER_STATUS_CHOICES:
                if choice[0] == self.status:
                    self.status_label = choice[1]
                    break

    def get_offer_percentage(self):
        return ((self.offer_amount * 100) / self.debt_amount).quantize(Decimal('.01'))


class Settlement(TrackedAbstractBase):
    settlement_id = models.AutoField(primary_key=True)
    settlement_offer = models.ForeignKey(SettlementOffer, related_name='settlements')
    payable_to = models.CharField(max_length=20)
    mail_to_company = models.EmailField(max_length=40)
    no_payments = models.BooleanField(default=False)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=4, choices=US_STATES)
    zip_code = models.CharField(max_length=10)
    creditor_reference = models.CharField(max_length=100, blank=True, null=True)  # Account # 5491100095397355: Jamie Ordaz
    phone = models.CharField(max_length=10, blank=True, null=True)
    letter_date = models.DateTimeField(blank=True, null=True)
    extra_info = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)


class BankAccount(TrackedAbstractBase):
    contact = models.OneToOneField(Contact, related_name='bank_account', primary_key=True)
    routing_number = models.CharField(max_length=20)
    account_number = models.CharField(max_length=30)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES)
    name_on_account = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'

    def info_complete(self):
        return True if self.bank_name and self.name_on_account and self.account_number and\
                       self.account_type and self.routing_number else False


MEMO_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('deferred_fees', 'Deferred Fees'),
    ('graduation_refund', 'Graduation Refund'),
    ('litigation_defense_fee', 'Litigation Defense Fee'),
    ('nsf_reschedule', 'NSF Reschedule'),
    ('recoop_transfer', 'Recoop of Transfer'),
    ('skip_reschedule', 'Skip Reschedule'),
    ('transfer', 'Transfer (will re-coop)'),
    ('transfer_refund', 'Transfer - Client/Creditor Refund'),
    ('webcorp_receivables', 'Webcorp Receivables'),
)

ACTION_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('schedule_transaction', 'Schedule Transaction'),
)

PAYMENT_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('ACH Client Debit', 'ACH Client Debit'),
    ('Earned Performance Fee', 'Earned Performance Fee'),
    ('Retained Performance Fee', 'Retained Performance Fee'),
    ('Client Refund', 'Client Refund'),
    ('Account Transfer', 'Account Transfer'),
    ('Check Payment', 'Check Payment'),
    ('Balance Transfer', 'Balance Transfer'),
)

PAYMENT_SUB_TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('ach_check_by_phone', 'ACH / Check By Phone'),
    ('advance_recoup', 'Advance Recoup'),
    ('bank_wire', 'Bank Wire'),
    ('check', 'Check'),
    ('check_2nd_day', 'Check 2nd Day'),
    ('check_overnight', 'Check Overnight'),
    ('direct_pay', 'DirectPay'),
    ('standard_check', 'Standard Check'),
    ('stop_payment_fee', 'Stop Payment Fee'),
)

SETTLEMENT_SUB_TYPE_CHOICES = (
    ('ach_check_by_phone', 'ACH / Check By Phone'),
    ('bank_wire', 'Bank Wire'),
    ('check', 'Check'),
    ('check_2nd_day', 'Check 2nd Day'),
    ('check_overnight', 'Check Overnight'),
)


PAYMENT_STATUS_CHOICES = (
    ('open', 'Open'),
    ('cleared', 'Cleared'),
    ('cancelled', 'Cancelled'),
)

PAYMENT_TRANSACTION_TYPE_CHOICES = (
    ('debit', 'Debit'),
    ('credit', 'Credit'),
)

PAYMENT_CHARGE_TYPE_CHOICES = (
    ('fee', 'Fee'),
    ('payment', 'Payment'),
    ('settlement', 'Settlement'),
)


class Payment(TrackedAbstractBase):
    active = models.BooleanField(default=True)
    payment_id = models.AutoField(primary_key=True)
    enrollment = models.ForeignKey(Enrollment, related_name='payments', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    cleared_date = models.DateTimeField(blank=True, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    type = models.CharField(max_length=40, blank=True, null=True)
    sub_type = models.CharField(max_length=40, choices=PAYMENT_SUB_TYPE_CHOICES, blank=True, null=True)
    memo = models.CharField(max_length=30, choices=MEMO_CHOICES, blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, blank=True, null=True)
    trans_id = models.CharField(max_length=20, blank=True, null=True)
    payee = models.ForeignKey(Payee, related_name='payments', blank=True, null=True)
    paid_to = models.ForeignKey(Payee, related_name='payments_received', blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    routing_number = models.CharField(max_length=20, blank=True, null=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=PAYMENT_TRANSACTION_TYPE_CHOICES, blank=True, null=True)
    charge_type = models.CharField(max_length=10, choices=PAYMENT_CHARGE_TYPE_CHOICES, default='payment')
    parent = models.ForeignKey('self', related_name='dependants', blank=True, null=True)
    associated_payment = models.ForeignKey('self', related_name='associated_payment_from', blank=True, null=True)
    associated_settlement_payment = models.ForeignKey('self', related_name='associated_settlement_payment_from', blank=True, null=True)
    settlement = models.ForeignKey(Settlement, related_name='settlement_payments', blank=True, null=True)
    added_manually = models.BooleanField(default=False)
    gateway = models.CharField(max_length=10, choices=CUSTODIAL_ACCOUNT_CHOICES, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'
        ordering = ['date']
        get_latest_by = 'created_at'

    def __init__(self, *args, **kwargs):
        super(Payment, self).__init__(*args, **kwargs)
        for type_choice in PAYMENT_TYPE_CHOICES:
            if type_choice[0] == self.type:
                self.type_label = type_choice[1]
                break
        for memo_choice in MEMO_CHOICES:
            if memo_choice[0] == self.memo:
                self.memo_label = memo_choice[1]
                break
        for status_choice in PAYMENT_STATUS_CHOICES:
            if status_choice[0] == self.status:
                self.status_label = status_choice[1]
                break

    def __str__(self):
        return self.type + ': ' + self.date.strftime(SHORT_DATE_FORMAT) + ' - ' + currency(self.amount)


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


class Activity(TrackedAbstractBase):
    activity_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='activities', blank=True, null=True)
    type = LongCharField(choices=ACTIVITY_TYPE_CHOICES)
    description = LongCharField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'

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


class Call(TrackedAbstractBase):
    call_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='calls', blank=True, null=True)
    type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    description = models.CharField(max_length=300, blank=True, null=True)
    duration = models.CharField(max_length=10, blank=True, null=True)
    phone_from = models.CharField(max_length=10, blank=True, null=True)
    phone_to = models.CharField(max_length=10, blank=True, null=True)
    event_type = models.CharField(max_length=12, choices=CALL_EVENT_TYPE_CHOICES, blank=True, null=True)
    result = models.CharField(max_length=20, choices=CALL_RESULT_TYPE_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'


@receiver(post_save, sender=Call)
def add_call_activity(sender, instance, **kwargs):
    activity = Activity(
        contact=instance.contact, type='call', description=instance.description, created_by=instance.created_by)
    activity.save()


EMAIL_TYPE_CHOICES = (
    ('manual', 'Manual'),
    ('automated', 'Automated'),
)


class Email(TrackedAbstractBase):
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

    class Meta:
        get_latest_by = 'created_at'


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


class Note(TrackedAbstractBase):
    note_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='notes', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES)
    cc = models.CharField(max_length=1000, blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'


@receiver(post_save, sender=Note)
def add_note_activity(sender, instance, **kwargs):
    activity = Activity(
        contact=instance.contact, type='note', description=instance.description, created_by=instance.created_by)
    activity.save()


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


class ESigned(TrackedAbstractBase):
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


class Signer(TrackedAbstractBase):
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


class Uploaded(TrackedAbstractBase):
    uploaded_id = models.AutoField(primary_key=True)
    contact = models.ForeignKey(Contact, related_name='uploaded_docs', blank=True, null=True)
    name = models.CharField(max_length=300)
    description = models.CharField(max_length=2000, blank=True, null=True)
    type = models.CharField(max_length=50, choices=UPLOADED_DOCUMENT_TYPE_CHOICES, blank=True, null=True)
    content = S3PrivateFileField(upload_to=uploaded_content_filename)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='uploaded_files', blank=True, null=True)

    class Meta:
        get_latest_by = 'created_at'

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


class Incomes(TrackedAbstractBase):
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


class Expenses(TrackedAbstractBase):
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


class DebtNote(TrackedAbstractBase):
    debt_note_id = models.AutoField(primary_key=True)
    debt = models.ForeignKey(Debt, related_name='notes', blank=True, null=True)
    content = models.CharField(max_length=2000, blank=True, null=True)


class Source(TrackedAbstractBase):
    source_id = models.AutoField(primary_key=True)
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


class Campaign(TrackedAbstractBase):
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

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return '%s' % self.title


def print_user(self):
    return self.get_full_name() if self.get_full_name() else self.username

User.add_to_class('__str__', print_user)


class GroupExtension(TrackedAbstractBase):
    group = models.OneToOneField(Group, related_name='extension', primary_key=True)
    parent = models.OneToOneField(Group, related_name='parent', blank=True, null=True)
    assignable = models.BooleanField(default=False)


class GroupMethods(Group):
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        super(GroupMethods, self).__init__(*args, **kwargs)
        self.parent = self.get_parent()
        self.assignable = self.get_assignable()

    def get_parent(self):
        return self.extension.parent if self.extension else None

    def get_assignable(self):
        return self.extension.assignable if self.assignable else None


@receiver(post_save, sender=Group)
def create_group_extension(sender, instance, created, **kwargs):
    if created:
        GroupExtension(group=instance).save()


class UserProfile(TrackedAbstractBase):
    related_user = models.OneToOneField(User)
    birthday = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=60, blank=True, null=True)
    state = models.CharField(max_length=4, choices=US_STATES, blank=True, null=True)
    city = models.CharField(max_length=60, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey(Company, related_name='users', blank=True, null=True)
    reports_to = models.ForeignKey(User, related_name='reports_to_me', blank=True, null=True)
    shared_user_data = models.ManyToManyField(User, related_name='sharing_data_with', blank=True)
    shared_with_all = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s' % self.related_user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile(related_user=instance).save()


for model in package_models(sundog.components):
    setattr(sys.modules[__name__], model.__name__, model)
