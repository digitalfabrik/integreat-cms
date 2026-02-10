from __future__ import annotations

from typing import ClassVar

from django.db import models


class SearchSuggestMixin(models.Model):
    """
    Mixin that provides search field configuration for the search suggestions feature.

    Models that include this mixin can define a ``search_fields`` class attribute
    to configure which fields are used for generating search suggestions and their
    relative weights.

    Example::

        class MyModel(AbstractBaseModel, SearchSuggestMixin):
            search_fields = {
                "title": {"weight": 2, "tokenize": False},
                "description": {"weight": 1, "tokenize": True},
            }

    The ``search_fields`` dict maps field names to configuration:
        - ``weight``: Higher values rank matches higher in suggestions (default: 1)
        - ``tokenize``: Whether to split field values into tokens (default: True)
    """

    search_fields: ClassVar[dict] = {}

    class Meta:
        abstract = True
