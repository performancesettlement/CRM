import copy
from itertools import chain
from django import forms
from django.contrib.auth.models import Group
from django.core.validators import validate_email
from django.db.models import Q
from django.utils.encoding import force_text
import pytz
from django_auth_app import enums
from sundog.models import Contact, Stage, Status, Campaign, Source, BankAccount, Note, Call,\
    Email, DEBT_SETTLEMENT, Uploaded, Incomes, Expenses, Creditor, Debt, DebtNote, EnrollmentPlan, FeePlan, FeeProfile,\
    FeeProfileRule, WorkflowSettings, Enrollment, AMOUNT_CHOICES, Payment, PAYMENT_TYPE_CHOICES, \
    CompensationTemplate, CompensationTemplatePayee, NONE_CHOICE_LABEL, Payee, COMPENSATION_TEMPLATE_PAYEE_TYPE_CHOICES, \
    AVAILABLE_FOR_CHOICES, COMPENSATION_TEMPLATE_TYPES_CHOICES, SettlementOffer, Settlement, Fee, Team

from sundog.constants import (
    SHORT_DATE_FORMAT,
    FIXED_VALUES,
)


DATE_INPUT_SETTINGS = {
    'format': SHORT_DATE_FORMAT,
    'attrs': {'placeholder': 'mm/dd/yyyy', 'data-provide': 'datepicker', 'data-date-autoclose': 'true'},
}


def get_date_input_settings(attrs=None):
    settings = copy.deepcopy(DATE_INPUT_SETTINGS)
    if attrs:
        settings['attrs'].update(attrs)
    return settings


EMPTY_LABEL = '--Select--'


class ContactForm(forms.ModelForm):

    class Meta:
        widgets = {
            'contact_id': forms.HiddenInput(),
        }
        model = Contact
        exclude = ['last_status_change', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].empty_label = EMPTY_LABEL
        self.fields['lead_source'].empty_label = EMPTY_LABEL
        self.fields['company'].empty_label = EMPTY_LABEL
        self.fields['stage'].empty_label = EMPTY_LABEL
        self.fields['status'].empty_label = EMPTY_LABEL
        self.fields['call_center_representative'].empty_label = EMPTY_LABEL

    def clean(self):
        if 'contact_id' in self.data:
            contact_id = int(self.data['contact_id'])
            self.cleaned_data['contact_id'] = contact_id


class ContactStatusForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = ['contact_id', 'stage', 'status']
        widgets = {
            'contact_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ContactStatusForm, self).__init__(*args, **kwargs)
        self.fields['status'].empty_label = EMPTY_LABEL
        self.fields['stage'].empty_label = EMPTY_LABEL
        self.fields['status'].required = True

        if args == (None,) and 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            self.fields['status'].queryset = Status.objects.filter(stage=instance.stage)
        elif args and args[0] and 'stage' in args[0]:
            stage_id = args[0]['stage']
            self.fields['status'].queryset = Status.objects.filter(stage__stage_id=stage_id)
        else:
            self.fields['status'].queryset = Status.objects.none()


class StageForm(forms.ModelForm):

    class Meta:
        model = Stage
        fields = ['name', 'stage_id', 'type']
        widgets = {
            'stage_id': forms.HiddenInput(),
            'type': forms.HiddenInput(),
        }


class StatusForm(forms.ModelForm):

    class Meta:
        model = Status
        fields = ['name', 'stage', 'color', 'status_id']
        widgets = {
            'status_id': forms.HiddenInput(),
        }

    def __init__(self, type=DEBT_SETTLEMENT, *args, **kwargs):
        super(StatusForm, self).__init__(*args, **kwargs)
        self.fields['stage'].queryset = self.fields['stage'].queryset.filter(type=type)
        self.fields['stage'].empty_label = EMPTY_LABEL


class WorkflowSettingsForm(forms.ModelForm):
    class Meta:
        model = WorkflowSettings
        fields = '__all__'
        widgets = {
            'on_submission': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_returned': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_reject': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_approval': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_second_approval': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_enrollment': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_de_enroll': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_re_enroll': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_graduation': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_un_graduate': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_dropped': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_contract_upload': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_first_payment_processed': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_first_payment_cleared': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_first_payment_return': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_final_payment': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'require_plan': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_bank': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_credit_card': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_bank_or_cc': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_debts': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_submit': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_contract_to_submit': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_contract_to_enroll': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'allow_reject': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_approval': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_secondary_approval': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_inc_exp': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'enforce_required_fields': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'require_comp_template': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'pause_on_nsf': forms.CheckboxInput(attrs={'class': 'col-xs-3 no-padding-sides'}),
            'on_pause': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_resume': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
            'on_returned_payment': forms.Select(attrs={'class': 'col-xs-6 no-padding-sides'}),
        }


class CampaignForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.fields['source'].empty_label = EMPTY_LABEL

    class Meta:
        model = Campaign
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'campaign_id': forms.HiddenInput(),
            'start_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'end_date': forms.DateInput(**DATE_INPUT_SETTINGS),
        }


class SourceForm(forms.ModelForm):

    class Meta:
        model = Source
        fields = ['name']


class BankAccountForm(forms.ModelForm):

    class Meta:
        model = BankAccount
        widgets = {
            'contact': forms.HiddenInput(),
        }
        exclude = ['created_at', 'updated_at', 'account_number_salt', 'account_number_last_4_digits']

    def __init__(self, *args, **kwargs):
        super(BankAccountForm, self).__init__(*args, **kwargs)
        self.previous_account_number = kwargs.get('instance').account_number if kwargs.get('instance') else None
        if kwargs and 'instance' in kwargs and not args:
            bank_account = kwargs['instance']
            if bank_account and bank_account.account_number:
                self.initial['account_number'] = '******' + bank_account.account_number[-4:]

    def save(self, commit=True):
        if self.instance:
            if self.cleaned_data and 'account_number' in self.cleaned_data:
                account_number = self.cleaned_data['account_number']
                if account_number == '******' + self.instance.account_number[-4:]:
                    self.cleaned_data['account_number'] = self.previous_account_number
                    self.instance.account_number = self.previous_account_number
        return super(BankAccountForm, self).save(commit=commit)


class NoteForm(forms.ModelForm):

    class Meta:
        model = Note
        widgets = {
            'contact': forms.HiddenInput(),
            'created_by': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'col-xs-12 no-padding', 'rows': 6}),
            'type': forms.Select(attrs={'class': 'col-xs-12 no-padding'}),
            'cc': forms.TextInput(attrs={'class': 'col-xs-12 no-padding'})
        }
        exclude = ['created_at']

    def __init__(self, contact, user, *args, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact
        self.fields['created_by'].initial = user


class CallForm(forms.ModelForm):
    minutes = forms.CharField(widget=forms.TextInput(attrs={'type': 'number', 'style': 'width: 70px;'}))
    seconds = forms.CharField(widget=forms.TextInput(attrs={'type': 'number', 'style': 'width: 70px;'}))
    contact_status = forms.ModelChoiceField(queryset=Status.objects.none())

    class Meta:
        model = Call
        widgets = {
            'contact': forms.HiddenInput(),
            'created_by': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'col-xs-12 no-padding', 'rows': 6})
        }
        exclude = ['created_at']

    def __init__(self, contact, user, *args, **kwargs):
        super(CallForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact
        self.fields['created_by'].initial = user
        self.fields['type'].initial = 'outgoing'
        self.fields['type'].empty_label = None
        self.fields['contact_status'].empty_label = None
        if contact.stage:
            self.fields['contact_status'].queryset = Status.objects.filter(stage=contact.stage)
        if contact.status:
            self.fields['contact_status'].initial = contact.status

    def save(self, commit=True):
        minutes = self.cleaned_data.pop('minutes')
        seconds = self.cleaned_data.pop('seconds')
        self.cleaned_data['duration'] = (minutes + ':' if minutes else '') + \
                                        ('0' if not seconds and minutes else seconds)
        return super(CallForm, self).save(commit=commit)


class MultiEmailField(forms.Field):
    def to_python(self, value):
        if not value:
            return []
        return value.split(',')

    def validate(self, value):
        super(MultiEmailField, self).validate(value)
        for email in value:
            validate_email(email)


class EmailForm(forms.ModelForm):
    file_upload = forms.FileField(required=False)
    emails_to = MultiEmailField(widget=forms.TextInput(attrs={'class': 'col-xs-12 no-padding'}))
    cc = MultiEmailField(required=False, widget=forms.TextInput(attrs={'class': 'col-xs-12 no-padding'}))

    class Meta:
        model = Email
        widgets = {
            'contact': forms.HiddenInput(),
            'email_from': forms.EmailInput(attrs={'class': 'col-xs-6 no-padding'}),
            'message': forms.Textarea(attrs={'class': 'col-xs-12 no-padding', 'id': 'message'}),
            'subject': forms.TextInput(attrs={'class': 'col-xs-12 no-padding'}),
        }
        exclude = ['created_at']

    def __init__(self, contact, user, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact
        self.fields['created_by'].initial = user

    def clean_emails_to(self):
        data = self.cleaned_data['emails_to']
        data = ','.join(data)
        return data


class UploadedForm(forms.ModelForm):
    class Meta:
        model = Uploaded
        widgets = {
            'contact': forms.HiddenInput(),
            'created_by': forms.HiddenInput(),
            'name': forms.HiddenInput(),
            'mime_type': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'class': 'col-xs-12 no-padding',
                                                 'style': 'max-width: 566px;min-height: 200px'}),
            'content': forms.FileInput(attrs={'style': 'padding-left: 3px;'}),
        }
        exclude = ['created_at']

    def __init__(self, contact, user, *args, **kwargs):
        super(UploadedForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact
        self.fields['created_by'].initial = user


class IncomesForm(forms.ModelForm):
    class Meta:
        model = Incomes
        widgets = {
            'contact': forms.HiddenInput(),
        }
        fields = '__all__'

    def __init__(self, contact, *args, **kwargs):
        super(IncomesForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact


class ExpensesForm(forms.ModelForm):
    class Meta:
        model = Expenses
        widgets = {
            'contact': forms.HiddenInput(),
        }
        fields = '__all__'

    def __init__(self, contact, *args, **kwargs):
        super(ExpensesForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact


class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        widgets = {
            'creditor_id': forms.HiddenInput(),
        }
        fields = '__all__'


class DebtForm(forms.ModelForm):
    note = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'style': 'resize: none;', 'class': 'form-control', 'maxlength': 2000}))

    class Meta:
        model = Debt
        widgets = {
            'debt_id': forms.HiddenInput(),
            'contact': forms.HiddenInput(),
            'last_payment_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'summons_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'court_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'discovery_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'answer_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'service_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'paperwork_received_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'poa_sent_date': forms.DateInput(**DATE_INPUT_SETTINGS),
        }
        fields = '__all__'

    def __init__(self, contact, *args, **kwargs):
        super(DebtForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact


class DebtNoteForm(forms.ModelForm):
    class Meta:
        model = DebtNote
        widgets = {
            'debt_id': forms.HiddenInput(),
            'debt': forms.HiddenInput(),
            'content': forms.Textarea(attrs={'class': 'col-xs-12 no-padding', 'style': 'resize: none;',
                                             'maxlength': 2000}),
        }
        fields = '__all__'


class EnrollmentPlanForm(forms.ModelForm):
    class Meta:
        model = EnrollmentPlan
        widgets = {
            'enrollment_plan_id': forms.HiddenInput(),
            'active': forms.CheckboxInput(),
            'two_monthly_drafts': forms.CheckboxInput(),
            'select_first_payment': forms.CheckboxInput(),
            'debt_amount_flag': forms.CheckboxInput(),
            'show_fee_subtotal_column': forms.CheckboxInput(),
            'savings_adjustment': forms.CheckboxInput(),
            'show_savings_accumulation': forms.CheckboxInput(),
            'states': forms.SelectMultiple(choices=enums.US_STATES, attrs={'class': 'col-xs-2 no-padding-sides',
                                                                           'style': 'height: 200px;'}),
            'fee_profile': forms.Select(attrs={'class': 'col-xs-2 no-padding-sides'})
        }
        fields = '__all__'


class EnrollmentForm(forms.ModelForm):
    first_date = forms.DateTimeField(required=False, widget=forms.DateInput(**DATE_INPUT_SETTINGS))

    class Meta:
        model = Enrollment
        widgets = {
            'enrollment_plan': forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}),
            'compensation_template': forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}),
            'start_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'second_date': forms.DateInput(**DATE_INPUT_SETTINGS),
            'contact': forms.HiddenInput(),
        }
        exclude = ['created_at', 'updated_at']

    def __init__(self, contact, *args, **kwargs):
        debt_ids = None
        if 'debt_ids' in kwargs:
            debt_ids = kwargs['debt_ids']
        super(EnrollmentForm, self).__init__(*args, **kwargs)
        self.fields['contact'].initial = contact
        queryset = EnrollmentPlan.objects.all()
        debt_amount = contact.total_enrolled_current_debts(ids=debt_ids)
        queryset.filter(Q(debt_amount_flag=False) | Q(debt_amount_flag=True, debt_amount_from__gte=debt_amount,
                                                      debt_amount_to__lte=debt_amount))
        self.fields['enrollment_plan'].queryset = queryset


FIELD_NAME_MAPPING = {
    'fixed_amount': 'amount',
    'percentage_amount': 'amount',
}


class FeePlanForm(forms.ModelForm):
    enrollment_plan = forms.ModelChoiceField(required=False, queryset=EnrollmentPlan.objects.all(),
                                             widget=forms.HiddenInput())
    fixed_amount = forms.DecimalField(required=False, widget=forms.TextInput(attrs={'style': 'max-width: 140px;'}))
    percentage_amount = forms.DecimalField(required=False, widget=forms.Select(choices=AMOUNT_CHOICES))

    class Meta:
        model = FeePlan
        widgets = {
            'fee_plan_id': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'style': 'max-width: 140px;'}),
        }
        fields = '__all__'

    def add_prefix(self, field_name):
        field_name = FIELD_NAME_MAPPING.get(field_name, field_name)
        return super(FeePlanForm, self).add_prefix(field_name)

    def __init__(self, *args, **kwargs):
        super(FeePlanForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.type in FIXED_VALUES:
                self.initial['fixed_amount'] = self.instance.amount
                self.fields['percentage_amount'].widget.attrs.update({'disabled': 'disabled', 'style': 'display:none;'})
            else:
                self.initial['percentage_amount'] = self.instance.amount
                self.fields['fixed_amount'].widget.attrs.update({'disabled': 'disabled',
                                                                 'style': 'max-width: 140px; display: none;'})


class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        widgets = {}
        fields = '__all__'


class FeeProfileForm(forms.ModelForm):
    class Meta:
        model = FeeProfile
        widgets = {}
        fields = '__all__'


class FeeProfileRuleForm(forms.ModelForm):
    class Meta:
        model = FeeProfileRule
        widgets = {}
        fields = '__all__'


class PaymentForm(forms.ModelForm):
    date = forms.DateTimeField(required=True, widget=forms.DateInput(**get_date_input_settings(
        {'class': 'col-xs-8 no-padding-sides'})))

    class Meta:
        model = Payment
        widgets = {
            'enrollment': forms.HiddenInput(),
            'active': forms.CheckboxInput(attrs={'style': 'height: 18px !important;'}),
            'type': forms.Select(choices=PAYMENT_TYPE_CHOICES, attrs={'class': 'col-xs-8 no-padding-sides'}),
            'sub_type': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'amount': forms.NumberInput(attrs={'class': 'col-xs-12 no-padding-sides'}),
            'account_number': forms.TextInput(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'routing_number': forms.TextInput(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'associated_settlement_payment': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'associated_payment': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'account_type': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'address': forms.Textarea(attrs={'class': 'col-xs-8 no-padding-sides', 'rows': 3}),
            'paid_to': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'payee': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'memo': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
            'action': forms.Select(attrs={'class': 'col-xs-8 no-padding-sides'}),
        }
        exclude = ['charge_type', 'transaction_type', 'parent', 'added_manually', 'trans_id', 'cleared_date',
                   'created_at', 'status']

    def __init__(self, *args, **kwargs):
        enrollment, sub_type_choices, attr_class = None, None, None
        if 'enrollment' in kwargs:
            enrollment = kwargs.pop('enrollment')
        if 'attr_class' in kwargs:
            attr_class = kwargs.pop('attr_class')
        if 'sub_type_choices' in kwargs:
            sub_type_choices = kwargs.pop('sub_type_choices')
        super(PaymentForm, self).__init__(*args, **kwargs)
        if enrollment:
            self.fields['associated_payment'].queryset = Payment.objects.filter(charge_type='payment',
                                                                                enrollment=enrollment)
            self.fields['associated_settlement_payment'].queryset = Payment.objects.filter(charge_type='settlement',
                                                                                           enrollment=enrollment)
        if attr_class:
            for _, field in self.fields.items():
                field.widget.attrs['class'] = attr_class
        if sub_type_choices:
            self.fields['sub_type'].choices = sub_type_choices

    def save(self, commit=True):
        self.cleaned_data['date'] = self.cleaned_data['date'].replace(tzinfo=pytz.utc)
        return super(PaymentForm, self).save(commit=commit)


class CompensationTemplateForm(forms.ModelForm):
    available_for = forms.ChoiceField(choices=AVAILABLE_FOR_CHOICES,
                                      widget=forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}))
    type = forms.ChoiceField(choices=COMPENSATION_TEMPLATE_TYPES_CHOICES,
                             widget=forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}))

    class Meta:
        model = CompensationTemplate
        widgets = {
            'name': forms.TextInput(attrs={'class': 'col-xs-12 no-padding-sides'})
        }
        exclude = ['company']

    def __init__(self, *args, **kwargs):
        super(CompensationTemplateForm, self).__init__(*args, **kwargs)


class CompensationTemplatePayeeForm(forms.ModelForm):

    payee = forms.ModelChoiceField(empty_label=NONE_CHOICE_LABEL, queryset=Payee.objects.all(),
                                   widget=forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}))
    type = forms.ChoiceField(choices=COMPENSATION_TEMPLATE_PAYEE_TYPE_CHOICES,
                             widget=forms.Select(attrs={'class': 'col-xs-12 no-padding-sides'}))

    class Meta:
        model = CompensationTemplatePayee
        widgets = {}
        exclude = ['compensation_template']


class RadioSelectNotNull(forms.RadioSelect):
    def get_renderer(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        str_value = force_text(value)
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        if choices[0][0] == '':
            choices.pop(0)
        return self.renderer(name, str_value, final_attrs, choices)


DISPLAYABLE_STATUSES_CHOICES = (
    ('in_review', 'In-Review'),
    ('declined', 'Declined'),
    ('accepted', 'Accepted'),
    ('client_auth_needed', 'Client Authorization is Needed'),
    ('sett_letter_needed', 'Settlement Letter is Needed'),
    ('client_auth_sett_letter_needed', 'Client Authorization and Settlement Letter are Needed'),
)


ATTRS_CLASS_COL_XS_3 = {'attrs': {'class': 'col-xs-3 no-padding-sides'}}

SETTLEMENT_DATE_INPUT_SETTINGS = copy.deepcopy(DATE_INPUT_SETTINGS)
SETTLEMENT_DATE_INPUT_SETTINGS.update(ATTRS_CLASS_COL_XS_3)


class SettlementOfferForm(forms.ModelForm):
    status = forms.ChoiceField(choices=DISPLAYABLE_STATUSES_CHOICES,
                               widget=forms.Select(**ATTRS_CLASS_COL_XS_3))

    class Meta:
        model = SettlementOffer
        widgets = {
            'negotiator': forms.Select(**ATTRS_CLASS_COL_XS_3),
            'made_by': RadioSelectNotNull(attrs={'style': 'margin: 0;'}),
            'notes': forms.Textarea(**ATTRS_CLASS_COL_XS_3),
            'date': forms.DateInput(**SETTLEMENT_DATE_INPUT_SETTINGS),
            'valid_until': forms.DateInput(**SETTLEMENT_DATE_INPUT_SETTINGS),
            'debt_amount': forms.NumberInput(**ATTRS_CLASS_COL_XS_3),
            'offer_amount': forms.NumberInput(**ATTRS_CLASS_COL_XS_3),
        }
        exclude = ['enrollment']

    def __init__(self, user, *args, **kwargs):
        super(SettlementOfferForm, self).__init__(*args, **kwargs)
        self.fields['status'].empty_label = None
        self.fields['negotiator'].empty_label = None
        self.fields['negotiator'].initial = user

    def _are_dates_valid(self):
        date = self.cleaned_data.get('date')
        valid_until = self.cleaned_data.get('valid_until')
        if date and valid_until and date > valid_until:
            self.add_error('date', 'Offer valid until date must be higher than offer date.')

    def _is_offer_value_valid(self):
        offer = self.cleaned_data.get('offer_amount')
        debt = self.cleaned_data.get('debt_amount')
        if offer > debt:
            self.add_error('offer', 'Offer amount must be lower than debt amount.')

    def full_clean(self):
        super(SettlementOfferForm, self).full_clean()
        self._are_dates_valid()
        self._is_offer_value_valid()


class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        widgets = {
            'extra_info': forms.Textarea(),
            'letter_date': forms.DateInput(**DATE_INPUT_SETTINGS),
        }
        exclude = ['settlement_offer']

ACTIVE_CHOICE = (
    (True, "Active"),
    (False, "Inactive"),
)


class AdjustPaymentForm(forms.Form):
    active_checkbox = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'enable-checkbox'}))
    active = forms.ChoiceField(required=False, choices=ACTIVE_CHOICE, widget=forms.Select())
    amount_checkbox = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'enable-checkbox'}))
    amount = forms.DecimalField(required=False, widget=forms.NumberInput())
    date_checkbox = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'enable-checkbox'}))
    date = forms.DateTimeField(required=False, widget=forms.DateInput(**DATE_INPUT_SETTINGS))
    memo_checkbox = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'enable-checkbox'}))
    memo = forms.CharField(required=False, widget=forms.TextInput())
    cancel_checkbox = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'cancel-checkbox'}))


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        widgets = {
            'parent': forms.Select(attrs={'class': 'col-xs-6 no-padding'}),
            'name': forms.TextInput(attrs={'class': 'col-xs-6'}),
            'assignable': forms.CheckboxInput(attrs={'class': 'no-margins'}),
        }
        exclude = ['permissions']

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['parent'].empty_label = EMPTY_LABEL


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        widgets = {
            'name': forms.TextInput(attrs={'class': 'col-xs-8'}),
            'users': forms.SelectMultiple(attrs={'class': 'col-xs-8 no-padding', 'size': 6}),
            'companies': forms.SelectMultiple(attrs={'class': 'col-xs-8 no-padding', 'size': 6}),
            'roles': forms.SelectMultiple(attrs={'class': 'col-xs-8 no-padding', 'size': 6}),
        }
        fields = '__all__'
