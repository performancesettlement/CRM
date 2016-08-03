import copy
import colorfield
from colorfield.fields import ColorWidget
from django import forms
from django.contrib.auth.models import User
from sundog.models import MyFile, FileStatus, Contact, Tag, ClientType, Stage, Status, STAGE_TYPE_CHOICES, \
    DEBT_SETTLEMENT, Campaign, Source, BankAccount
from sundog import services
from haystack.forms import SearchForm
from sundog.constants import RADIO_FILTER_CHOICES, SHORT_DATE_FORMAT
from sundog.utils import hash_password


class FileSearchForm(SearchForm):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'search', 'class': 'input-sm form-control',
                                                                      'placeholder': 'Search...'}))
    status = forms.ModelChoiceField(required=False, empty_label="Filter by File Status...",
                                    queryset=FileStatus.objects.none(),
                                    widget=forms.Select(attrs={'class': 'input-sm form-control input-s-sm inline'}))
    created_start = forms.DateField(required=False, widget=forms.DateInput(format=SHORT_DATE_FORMAT, attrs={'placeholder': 'Created from', 'class':'input-sm form-control'}))
    created_end = forms.DateField(required=False, widget=forms.DateInput(format=SHORT_DATE_FORMAT, attrs={'placeholder': 'mm/dd/yyyy', 'class':'input-sm form-control'}))
    sort_column = forms.CharField(required=False, widget=forms.HiddenInput())
    sort_asc = forms.CharField(required=False, widget=forms.HiddenInput())
    radio_field = forms.ChoiceField(required=False, widget=forms.RadioSelect, choices=RADIO_FILTER_CHOICES)

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super(FileSearchForm, self).search()

        if not self.is_valid():
            return self.no_query_found()

        # Filter by status
        if self.cleaned_data['status']:
            current_status = self.cleaned_data['status']
            sqs = sqs.filter(status=current_status.name)

        # Filter by created date
        if self.cleaned_data['created_start']:
            created_start_date = self.cleaned_data['created_start']
            sqs = sqs.filter(created_time__gte=created_start_date)

        if self.cleaned_data['created_end']:
            created_end_date = self.cleaned_data['created_end']
            sqs = sqs.filter(created_time__lte=created_end_date)

        if self.cleaned_data['sort_column'] and self.cleaned_data['sort_asc']:
            sort_column = self.cleaned_data['sort_column']
            sort_order = self.cleaned_data['sort_asc']
            if sort_column == "Id":
                if "sorting_asc" == sort_order:
                    sqs = sqs.order_by("file_id")
                else:
                    sqs = sqs.order_by("-file_id")
            elif sort_column == "File":
                if "sorting_asc" == sort_order:
                    sqs = sqs.order_by("sorted_description")
                else:
                    sqs = sqs.order_by("-sorted_description")
            elif sort_column == "Current Status":
                if "sorting_asc" == sort_order:
                    sqs = sqs.order_by("status")
                else:
                    sqs = sqs.order_by("-status")
            elif sort_column == "Priority":
                    if "sorting_asc" == sort_order:
                        sqs = sqs.order_by("priority")
                    else:
                        sqs = sqs.order_by("-priority")
            elif sort_column == "Completion":
                if "sorting_asc" == sort_order:
                    sqs = sqs.order_by("completion")
                else:
                    sqs = sqs.order_by("-completion")
        return sqs

    def no_query_found(self):
        return self.searchqueryset.all()


class FileForm(forms.ModelForm):
    description = forms.CharField(required=True, widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)
        self.fields['current_status'].queryset = services.get_status_list_by_user(self.current_user)
        self.fields['tags'].required = False
        self.fields['participants'].required = False

    class Meta:
        model = MyFile
        exclude = ('messages', 'creator_user_username', 'creator_user_full_name',  'created_time', 'last_update_time',
                   'last_update_user_username', 'last_update_user_full_name', 'file_status_history')


class ImpersonateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id']

    id = forms.ModelChoiceField(
        required=True, widget=forms.Select(attrs={'class': 'form-control'}), queryset=[])

    def __init__(self, id, *args, **kwargs):
        super(ImpersonateUserForm, self).__init__(*args, **kwargs)
        self.fields['id'].queryset = services.get_impersonable_users(id)


class FileCustomForm(forms.ModelForm):
    description = forms.CharField(required=True, widget=forms.Textarea(attrs={'class': 'form-control', 'maxlength': 1000}))
    current_status = forms.ModelChoiceField(required=True, queryset=FileStatus.objects.none(),
                                            label='',
                                            widget=forms.Select(attrs={'class': 'form-control',
                                                                       'onChange': 'updateCompleted(this)'}))

    client = forms.ModelChoiceField(required=True, queryset=Contact.objects.all(), empty_label="Select a Client...",
                                    widget=forms.Select(attrs={'class': 'chosen-select',
                                                               'data-placeholder': 'Select a Client...'}))

    tags = forms.ModelMultipleChoiceField(required=False, queryset=Tag.objects.all(),
                                          widget=forms.SelectMultiple(attrs={'class': 'chosen-select',
                                                                             'data-placeholder': 'Click to display...'}))

    quoted_date = forms.DateField(required=False, widget=forms.DateInput(format=SHORT_DATE_FORMAT,
                                                                         attrs={'placeholder': 'mm/dd/yyyy',
                                                                                'class': 'form-control'}))

    invoice_date = forms.DateField(required=False, widget=forms.DateInput(format=SHORT_DATE_FORMAT,
                                                                          attrs={'placeholder': 'mm/dd/yyyy',
                                                                                 'class': 'form-control'}))

    quoted_price = forms.DecimalField(required=False, decimal_places=2, widget=forms.NumberInput(attrs={'min': '0', 'max': '999999999999',
                                                                                      'class': 'form-control'}))
    invoice_price = forms.DecimalField(required=False, decimal_places=2, widget=forms.NumberInput(attrs={'min': '0', 'max': '999999999999',
                                                                                       'class': 'form-control'}))

    class Meta:
        model = MyFile
        exclude = ('participants', 'messages', 'creator_user_username', 'creator_user_full_name',  'created_time',
                   'last_update_time', 'last_update_user_username', 'last_update_user_full_name', 'file_status_history')

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

        if args and args[0] and 'stage' in args[0]:
            stage_id = args[0]['stage']
            self.fields['status'].queryset = Status.objects.filter(stage__stage_id=stage_id)
        else:
            if 'instance' in kwargs and kwargs['instance']:
                instance = kwargs['instance']
                self.fields['status'].queryset = Status.objects.filter(stage=instance.stage)
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


class CampaignForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.fields['source'].empty_label = EMPTY_LABEL

    class Meta:
        model = Campaign
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'campaign_id': forms.HiddenInput(),
            'start_date': forms.DateInput(format=SHORT_DATE_FORMAT,
                                          attrs={'placeholder': 'mm/dd/yyyy', 'data-provide': 'datepicker'}),
            'end_date': forms.DateInput(format=SHORT_DATE_FORMAT,
                                        attrs={'placeholder': 'mm/dd/yyyy', 'data-provide': 'datepicker'}),
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
            if bank_account and bank_account.account_number_last_4_digits:
                self.initial['account_number'] = '******' + bank_account.account_number_last_4_digits

    def save(self, commit=True):
        account_number_changed = True
        if self.instance:
            if self.cleaned_data and 'account_number' in self.cleaned_data:
                account_number = self.cleaned_data['account_number']
                if account_number == '******' + self.instance.account_number_last_4_digits:
                    account_number_changed = False
                    self.cleaned_data['account_number'] = self.previous_account_number
                    self.instance.account_number = self.previous_account_number
        if account_number_changed:
            hash_password(self.instance)
        return super(BankAccountForm, self).save(commit=commit)
