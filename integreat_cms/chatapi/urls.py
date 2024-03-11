from django.urls import path

from . import views

urlpatterns = [
    path("api/chat/message/", views.special_case_2003),
]

