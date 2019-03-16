"""
Handling of login, logout and password reset functionality.
"""
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.urls import reverse


def login(request):
    """View to provide login functionality
    Args:
            request: Object representing the user call
    Returns:
            HttpResponseRedirect: View function to render the Login page
    """
    return auth_views.LoginView.as_view(
        template_name='registration/login.html')(request)


def logout(request):
    """View to provide logout functionality
    Args:
            request: Object representing the user call
    Returns:
            HttpResponseRedirect: Redirect to the login page after logout
    """

    django_logout(request)
    messages.info(request, 'Sie wurden erfolgreich abgemeldet.')
    return HttpResponseRedirect(reverse('login'))


def password_reset_done(request):
    """View linked to the Password reset functionality
    Args:
            request: Object representing the user call
    Returns:
            HttpResponseRedirect: Redirect after password reset
    """

    messages.info(request, ('Eine Nachricht mit Anweisungen zum Zurücksetzen Ihres'
                            'Passwort wurde an die angegebene E-Mail Adresse geschickt.'))
    return HttpResponseRedirect(reverse('password_reset'))


def password_reset_confirm(request):
    """View linked to the Password reset functionality
    Args:
            request: Object representing the user call
    Returns:
            PasswordChangeDoneView: Linked to Template to build view for user
    """

    template = 'registration/password_reset_confirm.html'
    return auth_views.PasswordChangeDoneView(template_name=template)


def password_reset_complete(request):
    """View linked to the Password reset functionality
    Args:
            request: Object representing the user call
    Returns:
            HttpResponseRedirect: Redirect to login page after password is reseted
    """

    messages.success(request, 'Ihr Passwort wurde erfolgreich geändert.\
                                Sie können sich jetzt mit dem neuen Passwort einloggen.')
    return HttpResponseRedirect(reverse('login'))
