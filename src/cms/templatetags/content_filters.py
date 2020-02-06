import logging

from django import template

from ..models import Language

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_translation(instance, language_code):
    return instance.translations.filter(language__code=language_code).first()


@register.simple_tag
def translated_language_name(language_code):
    return Language.objects.get(code=language_code).translated_name

@register.simple_tag
def get_language(language_code):
    return Language.objects.get(code=language_code)

# Unify the language codes of backend and content languages
@register.simple_tag
def unify_language_code(language_code):
    if language_code == 'en-gb':
        return 'en-us'
    return language_code


@register.filter
def get_int_list(data, list_name):
    return [int(item) for item in data.getlist(list_name)]


@register.filter
def is_empty(iterable):
    return not bool(iterable)
