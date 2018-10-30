from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'current_menu_item': 'dashboard'})