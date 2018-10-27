from django import forms
from django.contrib.auth.forms import AuthenticationForm 


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username",
                               widget=forms.TextInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'username', 'name': 'username', 'placeholder': 'Benutzername'}))
    password = forms.CharField(label="Password",
                               widget=forms.PasswordInput(attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'password', 'name': 'password', 'placeholder': 'Passwort'}))