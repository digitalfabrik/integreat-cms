from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from ..util import auth


@login_required
def index(request):
    return render(request, 'dashboard.html')

def login(request):
    return auth_views.LoginView.as_view(template_name='login.html', authentication_form=auth.LoginForm)(request)

def logout(request):
    django_logout(request)
    messages.info(request, 'Sie wurden erfolgreich abgemeldet.')
    return  HttpResponseRedirect(reverse('login'))