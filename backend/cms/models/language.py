from django.core.validators import MinLengthValidator
from django.db import models


class Language(models.Model):
    code = models.CharField(max_length=2, primary_key=True, validators=[MinLengthValidator(2)])
    title = models.CharField(max_length=250)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
