from django.utils.text import slugify

from ...models import Page, Event


def generate_unique_slug(form_object, foreign_model=None):

    slug = form_object.cleaned_data['slug']

    # if slug is empty, generate from title/name
    if not slug:
        # determine fallback field of the model
        if foreign_model:
            fallback = 'title'
        else:
            fallback = 'name'
        # slugify to make sure slug doesn't contain special chars etc.
        slug = slugify(form_object.cleaned_data[fallback], allow_unicode=True)
        # If the title/name field didn't contain valid characters for a slug, we use a hardcoded fallback slug
        if not slug:
            slug = 'page'

    unique_slug = slug
    i = 1
    pre_filtered_objects = form_object.Meta.model.objects

    # if the foreign model is a content type (e.g. page or event), make sure slug is unique per region and language
    if foreign_model:
        try:
            foreign_instance = getattr(form_object.instance, foreign_model)
        except (Page.DoesNotExist, Event.DoesNotExist):
            return slug
        pre_filtered_objects = pre_filtered_objects.filter(**{
            foreign_model + '__region': foreign_instance.region,
            'language': form_object.instance.language
        })

    # generate new slug while it is not unique
    while True:
        # get other objects with same slug
        other_object = pre_filtered_objects.filter(
            slug=unique_slug
        )
        if foreign_model:
            # other objects which are just other versions of this object are allowed to have the same slug
            other_object = other_object.exclude(**{
                foreign_model: foreign_instance,
                'language': form_object.instance.language
            })
        else:
            # the current object is also allowed to have the same slug
            other_object = other_object.exclude(
                id=form_object.instance.id,
            )
        if not other_object.exists():
            break
        i += 1
        unique_slug = '{}-{}'.format(slug, i)

    return unique_slug
