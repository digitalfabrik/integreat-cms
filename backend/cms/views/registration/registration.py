from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def login(request):
    return auth_views.LoginView.as_view(
        template_name='registration/login.html')(request)


def logout(request):
    django_logout(request)
    messages.info(request, 'Sie wurden erfolgreich abgemeldet.')
    return HttpResponseRedirect(reverse('login'))


def password_reset_done(request):
    messages.info(request, ('Eine Nachricht mit Anweisungen zum Zurücksetzen Ihres'
                            'Passwort wurde an die angegebene E-Mail Adresse geschickt.'))
    return HttpResponseRedirect(reverse('password_reset'))


def password_reset_confirm(request):
    return auth_views.password_reset_confirm(
        request,
        template_name='registration/password_reset_confirm.html')


def password_reset_complete(request):
    messages.success(request, 'Ihr Passwort wurde erfolgreich geändert.\
        Sie können sich jetzt mit dem neuen Passwort einloggen.')
    return HttpResponseRedirect(reverse('login'))
