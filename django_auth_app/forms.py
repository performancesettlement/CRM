from django import forms
from django.contrib.auth import authenticate

MIN_LENGTH = 6


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
