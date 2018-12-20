from django.http import HttpResponse


def sites(request):
    return HttpResponse("Hello, world. You're at the API index.")
