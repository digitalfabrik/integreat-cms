from django.core.validators import MinLengthValidator
from django.db import models


class Language(models.Model):

    DIRECTION = (
        ('ltr', 'left-to-right'),
        ('rtl', 'right-to-left')
    )

    code = models.CharField(max_length=2, primary_key=True, validators=[MinLengthValidator(2)])
    title = models.CharField(max_length=250, blank=False)
    text_direction = models.CharField(choices=DIRECTION, max_length=3)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
