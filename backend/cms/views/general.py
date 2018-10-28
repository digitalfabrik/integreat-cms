from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(request, 'dashboard.html')

def handler400(request):
    ctx = {'code': 400, 'title': 'Bad request', 'message': 'Die Anfrage war fehlerhaft aufgebaut.'}
    response = render(request, 'http_error.html', ctx)
    response.status_code = 400
    return response

def handler403(request):
    ctx = {'code': 403, 'title': 'Forbidden', 'message': 'In der Anfrage wurde nicht die notwendige Berechtigung übermittelt.'}
    response = render(request, 'http_error.html', ctx)
    response.status_code = 403
    return response

def handler404(request):
    ctx = {'code': 404, 'title': 'Seite nicht gefunden', 'message': 'Die von Ihnen angeforderte Seite konnte leider nicht gefunden werden.'}
    response = render(request, 'http_error.html', ctx)
    response.status_code = 404
    return response

def handler500(request):
    ctx = {'code': 500, 'title': 'Internal Server Error', 'message': 'Es ist ein unerwarteter Fehler aufgetreten.'}
    response = render(request, 'http_error.html', ctx)
    response.status_code = 500
    return response

def csrf_failure(request):
    return render(request, 'csrf_failure.html')