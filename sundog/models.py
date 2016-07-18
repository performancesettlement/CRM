import hashlib
from colorfield.fields import ColorField
from colorful.fields import RGBColorField
from django.db import models
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from sundog.utils import document_directory_path, format_price
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


STAGE_TYPE_CHOICES = (
    ('debt_settlement', 'Debt Settlement'),
    ('student_loans', 'Student Loans'),
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
    stage = models.ForeignKey(Stage, blank=True, null=True)
    status = models.ForeignKey(Status, blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        permissions = (
            ("import_clients", "Can import clients"),
        )

    def full_name(self):
        full_name = self.first_name if self.first_name.strip() else ""
        full_name += (" " if full_name and self.last_name else "") + (self.last_name if self.last_name.strip() else "")
        return full_name

    def __str__(self):
        return '%s' % self.first_name

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
