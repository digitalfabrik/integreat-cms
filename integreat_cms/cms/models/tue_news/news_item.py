from django.db import models

from .news_category import NewsCategory
from .news_language import NewsLanguage


class NewsItem(models.Model):
    """
    Actual TuNews
    """

    title = models.CharField("Titel", max_length=200)
    content = models.TextField("Inhalt")
    enewsno = models.CharField("E-News Nummer", max_length=20)
    pub_date = models.DateTimeField("Datum")
    newscategory = models.ManyToManyField(NewsCategory)
    language = models.ForeignKey(NewsLanguage, on_delete=models.CASCADE)
    wppostid = models.IntegerField("WP Post ID", null=True, unique=True)
    translations = models.JSONField("Übersetzungen", null=True, blank=True)

    class Meta:
        verbose_name = "Nachricht"
        verbose_name_plural = "Nachrichten"
        ordering = ["-enewsno"]

    def __str__(self) -> str:
        return self.language.language + ": " + self.title + " - " + self.enewsno
