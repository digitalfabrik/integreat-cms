from django.http import HttpResponse

from .request_sender import (
    send_offer,
)
from .utils import (
    update_cms_data,
)


def test(request):
    return HttpResponse("test")


def test_send_offer(request):
    domain = "localhost:8000"
    send_offer(domain)
    return HttpResponse("Angebot gesendet.")


def test_update(request):
    update_cms_data()
    return HttpResponse("Alles upgedatet.")


def test_ask(request):
    return HttpResponse("Hier passiert nichts")
