from django.db import models


class NewsCategory(models.Model):
    """
    News categories
    """

    name = models.CharField("Kategorie", max_length=200)

    class Meta:
        verbose_name = "Nachrichtenkategorie"
        verbose_name_plural = "Nachrichtenkategorien"

    def __str__(self) -> str:
        return self.name
