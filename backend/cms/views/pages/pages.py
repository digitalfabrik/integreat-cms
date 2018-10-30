from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def pages(request):
    return render(request, 'pages/tree_view.html', {'current_menu_item': 'pages'})