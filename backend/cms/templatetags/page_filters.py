from django import template

register = template.Library()

@register.filter
def page_translation_title(page, language):
    all_page_translations = page.page_translations
    page_translation = all_page_translations.filter(language__code=language.code)
    if page_translation.exists():
        return page_translation.first()
    return all_page_translations.first()
