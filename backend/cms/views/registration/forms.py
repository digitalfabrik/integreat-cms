from django import forms as django_forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm


class LoginForm(AuthenticationForm):
    username = django_forms.CharField(widget=django_forms.TextInput(
        attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'username', 'name': 'username', 'placeholder': 'Benutzername'}))
    password = django_forms.CharField(widget=django_forms.PasswordInput(
        attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'password', 'name': 'password', 'placeholder': 'Passwort'}))


class PasswordResetForm(DjangoPasswordResetForm):
    email = django_forms.EmailField(widget=django_forms.EmailInput(
        attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'email', 'name': 'email', 'placeholder': 'E-Mail'}))


class PasswordResetConfirmForm(SetPasswordForm):
    error_messages = {
        'password_mismatch': "Die Passwörter stimmen nicht überein.",
    }

    new_password1 = django_forms.CharField(widget=django_forms.PasswordInput(
        attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'new_password1', 'name': 'new_password1', 'placeholder': 'Passwort'}))
    new_password2 = django_forms.CharField(widget=django_forms.PasswordInput(
        attrs={'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker leading-tight focus:outline-none focus:shadow-outline', 'id': 'new_password2', 'name': 'new_password2', 'placeholder': 'Passwort wiederholen'}))
