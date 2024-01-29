"""
This is a collection of tags and filters which are useful for all models.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from ..models.abstract_base_model import AbstractBaseModel

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_model_verbose_name(instance: AbstractBaseModel) -> str:
    """
    This tag returns the readable name of an instance's model.

    :param instance: The model object instance
    :return: The verbose name of the model
    """
    return instance._meta.verbose_name
