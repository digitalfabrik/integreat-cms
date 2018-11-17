from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def archive(request):
    return render(request, 'pages/archive.html',
                  {'current_menu_item': 'pages'})
