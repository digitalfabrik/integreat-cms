from django.db import models

# Create your models here.

class ChatSession(models.Model):
    session_token = models.CharField(max_length=200)
    zammad_ticket_id = models.IntegerField()
