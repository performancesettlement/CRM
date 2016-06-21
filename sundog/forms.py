from django import forms
from django.contrib.auth.models import User
from sundog.models import MyFile, FileStatus, Client, Tag, ClientType
from sundog import services
from haystack.forms import SearchForm
from sundog.constants import RADIO_FILTER_CHOICES, SHORT_DATE_FORMAT


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

    client = forms.ModelChoiceField(required=True, queryset=Client.objects.all(), empty_label="Select a Client...",
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


class ClientForm(forms.ModelForm):
    client_type = forms.ModelChoiceField(queryset=ClientType.objects.all(), empty_label="Select a Client Type...",
                                         widget=forms.Select(attrs={'class': 'chosen-select',
                                                                    'data-placeholder': 'Select a Client Type...'}))

    # client_id = forms.HiddenInput()

    class Meta:
        widgets = {
            "client_id": forms.HiddenInput()
        }
        model = Client
        exclude = ('active',)

    def clean(self):
        name = self.cleaned_data.get('name')
        client_id = None
        if 'client_id' in self.data:
            client_id = int(self.data.get('client_id'))
            self.cleaned_data["client_id"] = client_id

        if name:
            name = str(name).upper().strip()
            pk = services.check_client_exists(name, client_id)
            if pk:
                self.add_error('name', "This name already exists in the system.")

        identification = self.cleaned_data.get('identification')
        if identification:
            identification = str(identification).upper().strip()
            pk = services.check_client_exists_by_identification(identification, client_id)
            if pk:
                self.add_error('identification', "This identification already exists in the system.")