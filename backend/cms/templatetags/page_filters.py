from django import template

register = template.Library()


@register.filter
def page_translation_title(page, language):
    all_page_translations = page.page_translations
    page_translation = all_page_translations.filter(language__code=language.code)
    if page_translation.exists():
        return page_translation.first().title
    elif all_page_translations.exists():
        page_translation = all_page_translations.first()
        return '{title} ({language})'.format(
            title=page_translation.title,
            language=page_translation.language
        )
    return ''


@register.filter
def page_translation_creator(page, language):
    all_page_translations = page.page_translations
    page_translation = all_page_translations.filter(language__code=language.code)
    if page_translation.exists():
        return page_translation.first().creator
    elif all_page_translations.exists():
        page_translation = all_page_translations.first()
        return '{creator} ({language})'.format(
            creator=page_translation.creator,
            language=page_translation.language
        )
    return ''


@register.filter
def page_translation_last_updated(page, language):
    all_page_translations = page.page_translations
    page_translation = all_page_translations.filter(language__code=language.code)
    if page_translation.exists():
        return page_translation.first().last_updated
    elif all_page_translations.exists():
        return all_page_translations.first().last_updated
    return ''


@register.filter
def page_translation_created_date(page, language):
    all_page_translations = page.page_translations
    page_translation = all_page_translations.filter(language__code=language.code)
    if page_translation.exists():
        return page_translation.first().created_date
    elif all_page_translations.exists():
        return all_page_translations.first().created_date
    return ''
