from django import template

from ..models import Language

register = template.Library()


@register.simple_tag
def get_page_translation(page, language_code):
    return page.page_translations.filter(language__code=language_code).first()


# Unify the language codes of backend and content languages
@register.simple_tag
def unify_language_code(language_code):
    if language_code == 'en-us':
        return 'en-gb'
    return language_code


@register.simple_tag
def translated_language_name(language_code):
    return Language.objects.get(code=language_code).translated_name


@register.simple_tag
def get_last_root_page(pages):
    return pages.filter(parent=None).last()


@register.filter
def get_descendants(page):
    return [descendant.id for descendant in page.get_descendants(include_self=True)]
