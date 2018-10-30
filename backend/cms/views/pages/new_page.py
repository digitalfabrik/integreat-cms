from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def new_page(request):
    return render(request, 'pages/new_page.html', {'current_menu_item': 'pages'})