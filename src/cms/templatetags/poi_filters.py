from django import template

register = template.Library()


@register.filter
def poi_translation_title(poi, language):
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__code=language.code)
    if poi_translation.exists():
        return poi_translation.first().title
    if all_poi_translations.exists():
        poi_translation = all_poi_translations.first()
        return f'{poi_translation.title} ({poi_translation.language})'
    return ''
