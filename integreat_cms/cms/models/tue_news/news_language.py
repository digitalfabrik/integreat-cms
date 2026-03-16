from django.db import models


class NewsLanguage(models.Model):
    """
    Languages used in Tü News
    """

    language = models.CharField("Sprache", max_length=200)
    code = models.CharField("Sprachcode", max_length=5)
    wpcategory = models.IntegerField("WordPress-Kategorie-ID", null=True, unique=True)

    class Meta:
        verbose_name = "Sprache"
        verbose_name_plural = "Sprachen"

    def __str__(self) -> str:
        return self.language
