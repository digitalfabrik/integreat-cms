"""
Django model decorators can be used to modify inherited fields of abstract models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.db.models.base import ModelBase


def modify_fields(**kwargs: Any) -> Callable:
    r"""
    This decorator can be used to override properties of inherited django model fields.

    :param \**kwargs: A mapping from model fields to their overridden key/value pairs
    :return: The decorated class
    """

    def wrap(cls: ModelBase) -> ModelBase:
        """
        The inner function for this decorator

        :param cls: The Django model
        :return: The decorated model class
        """
        for field, prop_dict in kwargs.items():
            for prop, val in prop_dict.items():
                setattr(cls._meta.get_field(field), prop, val)
        return cls

    return wrap
