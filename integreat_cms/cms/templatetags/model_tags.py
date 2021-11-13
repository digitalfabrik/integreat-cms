"""
This is a collection of tags and filters which are useful for all models.
"""
import logging

from django import template

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_model_verbose_name(instance):
    """
    This tag returns the readable name of an instance's model.

    :param instance: The model object instance
    :type instance: ~django.db.models.Model

    :return: The verbose name of the model
    :rtype: str
    """
    return instance._meta.verbose_name
