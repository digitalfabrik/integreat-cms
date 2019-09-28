from django.utils.text import slugify


def generate_unique_slug(form_object_instance, foreign_model=None):

    slug = form_object_instance.cleaned_data['slug']

    # if slug is empty, generate from title/name
    if not slug:
        # determine fallback field of the model
        if foreign_model:
            fallback = 'title'
        else:
            fallback = 'name'
        # slugify to make sure slug doesn't contain special chars etc.
        slug = slugify(form_object_instance.cleaned_data[fallback])

    unique_slug = slug
    i = 1
    pre_filtered_objects = form_object_instance.Meta.model.objects

    # if the foreign model is a content type (e.g. page or event), make sure slug is unique per region and language
    if foreign_model:
        pre_filtered_objects = pre_filtered_objects.filter(**{
            foreign_model + '__region': form_object_instance.region,
            'language': form_object_instance.language
        })

    # generate new slug while it is not unique
    while True:
        other_object = pre_filtered_objects.filter(
            slug=unique_slug
        ).exclude(
            id=form_object_instance.instance.id
        )
        if not other_object.exists():
            break
        i += 1
        unique_slug = '{}-{}'.format(slug, i)

    return unique_slug
