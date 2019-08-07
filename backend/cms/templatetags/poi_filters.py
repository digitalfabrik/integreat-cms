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
        return '{title} ({language})'.format(
            title=poi_translation.title,
            language=poi_translation.language
        )
    return ''


@register.filter
def poi_translation_creator(poi, language):
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__code=language.code)
    if poi_translation.exists():
        return poi_translation.first().creator
    if all_poi_translations.exists():
        poi_translation = all_poi_translations.first()
        return '{creator} ({language})'.format(
            creator=poi_translation.creator,
            language=poi_translation.language
        )
    return ''


@register.filter
def poi_translation_last_updated(poi, language):
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__code=language.code)
    if poi_translation.exists():
        return poi_translation.first().last_updated
    if all_poi_translations.exists():
        return all_poi_translations.first().last_updated
    return ''


@register.filter
def poi_translation_created_date(poi, language):
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__code=language.code)
    if poi_translation.exists():
        return poi_translation.first().created_date
    if all_poi_translations.exists():
        return all_poi_translations.first().created_date
    return ''
