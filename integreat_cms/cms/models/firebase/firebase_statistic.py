from django.db import models

from integreat_cms.cms.models.abstract_base_model import AbstractBaseModel


class FirebaseStatistic(AbstractBaseModel):
    """
    Data model representing a push notification translation
    """

    date = models.DateField()
    region = models.CharField(max_length=100)
    language_slug = models.CharField(max_length=2)
    count = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.date} - {self.region} - {self.language_slug} - {self.count}"

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method and is used for logging.

        :return: The canonical string representation of the firebase statistic
        """
        return (
            f"<FirebaseStatistic ({self.date} - {self.region} - {self.language_slug})>"
        )
