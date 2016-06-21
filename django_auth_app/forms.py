from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django_auth_app.models import UserProfile
from django_auth_app import enums
import string


MIN_LENGTH = 6


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label='', widget=forms.TextInput(attrs={'placeholder': 'Email *', 'class': 'form-control', 'required': ''}))
    username = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Username *', 'class': 'form-control', 'required': ''}))
    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password *', 'class': 'form-control', 'required': ''}))
    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password *', 'class': 'form-control', 'required': ''}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name *', 'required': ''}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name *', 'required': ''}))

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2', 'first_name', 'last_name')

    def clean(self):
        super(RegistrationForm, self).clean()
        password1 = self.cleaned_data.get('password1')

        if len(password1) < MIN_LENGTH:
            self.add_error('password1', "Password must be at least %d characters long." % MIN_LENGTH)

        # check for digit
        if not any(char.isdigit() for char in password1):
            self.add_error('password1', "Password must container at least 1 digit.")

            # check for letter
        if not any(char.isalpha() for char in password1):
            self.add_error('password1', "Password must container at least 1 letter.")

        invalid_chars = set(string.punctuation)
        if not any(char in invalid_chars for char in password1):
            self.add_error('password1', "Password must container at least 1 special character.")

        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username').strip().lower()
        if email and User.objects.filter(email=email).exclude(username=username).count():
            self.add_error('email', 'Email addresses must be unique.')
        return self.cleaned_data

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = user.username.strip().lower()
        if commit:
            user.save()

        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        username = self.cleaned_data.get('username').strip().lower()
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError("Sorry, that login was invalid. Please try again.")
        if not user.is_active:
            raise forms.ValidationError("You have to activate the account.")
        return self.cleaned_data

    def login(self, request):
        username = self.cleaned_data.get('username').strip().lower()
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        return user


class RecoverForm(forms.Form):
    email = forms.CharField(max_length=255, required=True)
    
    def clean(self):
        email = self.cleaned_data.get('email')
        user = None
        try:
            validate_email(email)
        except:
            self.add_error('email', "The email format is invalid.")
        try:
            user = User.objects.get(email=email)
        except:
            pass

        if not user:
            self.add_error('email', "No user with that email.")
        return self.cleaned_data


class ConfirmRecoverForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder': 'Password *', 'required':''}), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder': 'Repeat password *', 'required':''}), required=True)
    recover_key = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        # validate if passwords are equal
        if password1 != password2:
            raise forms.ValidationError("The two password fields must be equal.")

        if len(password1) < MIN_LENGTH:
            self.add_error('password1', "Password must be at least %d characters long." % MIN_LENGTH)

        # check for digit
        if not any(char.isdigit() for char in password1):
            self.add_error('password1', "Password must container at least 1 digit.")

        # check for letter
        if not any(char.isalpha() for char in password1):
            self.add_error('password1', "Password must container at least 1 letter.")

        invalid_chars = set(string.punctuation)
        if not any(char in invalid_chars for char in password1):
            self.add_error('password1', "Password must container at least 1 special character.")
        
        # validate if recover_token exists
        recover_key = self.cleaned_data.get('recover_key')
        
        if not recover_key:
            raise forms.ValidationError("The recover key is empty.")

        user_profile = None
        try:
            user_profile = UserProfile.objects.get(recover_key= "%s" % recover_key)
        except:
            pass

        if user_profile is None:
            raise forms.ValidationError("The recover key is invalid.")

        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}))
    middle_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle name'}))
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control', 'readonly': ''}))
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control', 'readonly': ''}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control phone-us'}))
    birthday = forms.DateField(required=False, widget=forms.DateInput(format="%m/%d/%Y", attrs={'placeholder': 'Birthday (mm/dd/yyyy)', 'class': 'form-control'}))
    state = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-control'}), choices=enums.US_STATES_R)
    timezone = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'form-control', 'required': ''}), choices=enums.FORMATTED_TIMEZONES)
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}))
    zip_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Zip code', 'class':'form-control zip-code'}))
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Country', 'class':'form-control'}))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Address', 'class':'form-control'}))
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Website', 'class':'form-control'}))
    twitter = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Twitter', 'class':'form-control'}))
    facebook = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Facebook', 'class':'form-control'}))
    linkedin = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Linkedin', 'class':'form-control'}))
    about = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'About', 'class': 'form-control'}))
    gender = forms.TypedChoiceField(choices=enums.GENDER_CHOICES, widget=forms.RadioSelect, coerce=int, required=False)

    class Meta:
        model = UserProfile
        fields = ('timezone', 'phone_number', 'birthday', 'middle_name', 'first_name', 'last_name',
                  'zip_code', 'address', 'city', 'state', 'country')
