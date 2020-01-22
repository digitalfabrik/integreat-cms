from django.http import JsonResponse

from cms.models import Accommodation, AccommodationTranslation, Region


def transform_accommodation(accommodation: Accommodation, translation: AccommodationTranslation):
    return {
        'name': translation.title,
        'current_language': translation.language.code,
        'description': translation.description,
        'short_description': translation.short_description,
        'opening_hours': {
            'from': accommodation.intake_from,
            'to': accommodation.intake_to
        },
        'address': {
            'street': accommodation.address,
            'plz': accommodation.postcode,
            'city': accommodation.city,
            'geo': {
                'lat': accommodation.latitude,
                'long': accommodation.longitude
            }
        },
        'phone': {
            'home': accommodation.phone_number,
            'mobile': accommodation.mobile_number
        },
        'sanitary_amenities': {
            'wc': accommodation.wc_available,
            'shower': accommodation.shower_available
        },
        'rules': {
            'animals': accommodation.animals_allowed,
            'shelter_seeking_person_intoxicated': accommodation.intoxicated_allowed,
            # TODO The following fields are dummy for now
            'female_only': False,
            'families_welcome': False,
            'male_only': False,
            'kids_welcome': False
        },
        'spoken_languages': [
            {
                'translated': spoken.translated_name,
                'code': spoken.code,
                'native': spoken.native_name
            }
            for spoken in accommodation.spoken_languages.all()],
        'institution': {
            "slug": accommodation.institution.slug,
            "name": accommodation.institution.name,
            "thumbnail": accommodation.institution.thumbnail
        },
        'beds': [
            {
                'target_group': bed.target_group.name,
                'num_beds': bed.num_beds,
                'num_free_beds': bed.num_free_beds
            }
            for bed in accommodation.beds.all()
        ]

    }


def accommodations(request, region_slug, language_code):
    _accommodations = Accommodation.objects.filter(region__slug=region_slug, archived=False)
    region = Region.objects.get(slug=region_slug)
    result = []
    for accommodation in _accommodations:
        translation = accommodation.get_translation(language_code=language_code)
        if not translation:
            translation = accommodation.get_translation(region.default_language.code)
        result.append(transform_accommodation(accommodation, translation))
    return JsonResponse(result, safe=False)  # Turn off Safe-Mode to allow serializing arrays
