from django.db import models


class TruncatingCharField(models.CharField):
    """
    Custom model field for CharFields that need to be truncated
    This is necessary in cases where we append a suffix and need to ensure to not exceed the limit and get a `DataError`.
    """

    def get_prep_value(self, value: str) -> str | None:
        value = super().get_prep_value(value)

        if value and len(value) > self.max_length:
            return value[: self.max_length - 3] + "..."
        return value
