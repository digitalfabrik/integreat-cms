from django import template
from django.conf import settings

register = template.Library()


@register.filter
def in_list(value, comma_separated_list):
    """
    This filter checks whether a given string value is contained in a comma separated list

    :param value: The value which should be checked
    :type value: str

    :param comma_separated_list: The list of comma-separated strings
    :type comma_separated_list: str

    :return: Whether or not value is contained in the list
    :rtype: bool
    """
    return value in comma_separated_list.split(",")


@register.filter
def get_private_member(element, key):
    """
    This filter returns a private member of an element

    :param element: The requested object
    :type element: object

    :param key: The key of the private variable (without the leading underscore)
    :type key: str

    :return: The value of the private variable
    :rtype: object
    """
    return element[f"_{key}"]


@register.simple_tag
def get_mt_visibility(region, perms):
    """
    This tag checks whether either DEEPL or SUMM.AI is activated in the region and the user has permission to manage automatic translations.

    :param region: The rcurrent region
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param perms: Permission of the user
    :type perms: ~django.contrib.auth.context_processors.PermWrapper

    :return: Whether the MT section should be shown
    :rtype: bool
    """
    return "cms.manage_translations" in perms and (
        settings.DEEPL_ENABLED or settings.SUMM_AI_ENABLED and region.summ_ai_enabled
    )
