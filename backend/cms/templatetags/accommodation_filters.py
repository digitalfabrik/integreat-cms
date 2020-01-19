from django import template

register = template.Library()


@register.filter
def accommodation_translation_title(accommodation, language):
    all_accommodation_translations = accommodation.accommodation_translations
    accommodation_translation = all_accommodation_translations.filter(language__code=language.code)
    if accommodation_translation.exists():
        return accommodation_translation.first().title
    if all_accommodation_translations.exists():
        accommodation_translation = all_accommodation_translations.first()
        return '{title} ({language})'.format(
            title=accommodation_translation.title,
            language=accommodation_translation.language
        )
    return ''
