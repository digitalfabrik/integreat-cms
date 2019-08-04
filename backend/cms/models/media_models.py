from django.db import models
from django import forms


class Document(models.Model):

    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.document.name

    # pylint: disable=W0221
    def delete(self, *args, **kwargs):
        self.document.delete()
        super().delete(*args, **kwargs)

    class Meta:
        default_permissions = ()


class DocumentForm(forms.ModelForm):

    class Meta:
        model = Document
        fields = ('description', 'document', )
