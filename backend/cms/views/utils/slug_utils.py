from django.utils.text import slugify


def generate_unique_slug(form_object_instance, foreign_model):

    slug = form_object_instance.cleaned_data['slug']
    # if slug is empty, generate from title
    if not slug:
        # slugify to make sure slug doesn't contain special chars etc.
        slug = slugify(form_object_instance.cleaned_data['title'])

    # make sure slug is unique per region and language
    unique_slug = slug
    i = 1
    while True:
        other_translation = form_object_instance.Meta.model.objects.filter(**{
            foreign_model + '__region': form_object_instance.region,
            'language': form_object_instance.language,
            'slug': unique_slug
        }).exclude(id=form_object_instance.instance.id)
        if not other_translation.exists():
            break
        i += 1
        unique_slug = '{}-{}'.format(slug, i)

    return unique_slug
