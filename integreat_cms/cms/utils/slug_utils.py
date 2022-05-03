"""
This module contains helpers regarding unique string identifiers without special characters ("slugs").
"""

import logging

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


def generate_unique_slug_helper(form_object, foreign_model):
    """
    This function acts like an interface and extracts all parameters of the form_object before actually generating
    the unique slug, so that unique slug generation can be performed without any cleaned form data after a form submission.

    :param form_object: The form which contains the slug field
    :type form_object: ~django.forms.Form

    :param foreign_model: If the form instance has a foreign key to another model (e.g. because it is a translation of
                          a content-object), this parameter contains the model of the foreign related object.
    :type foreign_model: str

    :raises ~django.core.exceptions.ValidationError: When no slug is given and there is also no field which can be used
                                                     as fallback (either ``title`` or ``name``).

    :return: An unique slug identifier
    :rtype: str
    """
    kwargs = {
        "slug": form_object.cleaned_data["slug"],
        "cleaned_data": form_object.cleaned_data,
        "manager": form_object.Meta.model.objects,
        "object_instance": form_object.instance,
        "foreign_model": foreign_model,
        "fallback": "name",
    }
    if foreign_model in ["page", "event", "poi"]:
        kwargs.update(
            {
                "region": form_object.instance.foreign_object.region,
                "language": form_object.instance.language,
                "fallback": "title",
            }
        )
    return generate_unique_slug(**kwargs)


def generate_unique_slug(**kwargs):
    r"""
    This function can be used in :mod:`~integreat_cms.cms.forms` to clean slug fields. It will make sure the slug field contains a
    unique identifier per region and language. It can also be used for region slugs (``foreign_model`` is ``None`` in
    this case). If the slug field is empty, it creates a fallback value from either the ``title`` or the ``name`` field.
    In case the slug exists already, it appends a counter which is increased until the slug is unique.

    Example usages:

    * :func:`~integreat_cms.cms.forms.regions.region_form.RegionForm.clean_slug`
    * :func:`~integreat_cms.cms.forms.pages.page_translation_form.PageTranslationForm.clean_slug`
    * :func:`~integreat_cms.cms.forms.events.event_translation_form.EventTranslationForm.clean_slug`
    * :func:`~integreat_cms.cms.forms.pois.poi_translation_form.POITranslationForm.clean_slug`

    :param \**kwargs: The supplied keyword arguments
    :type \**kwargs: dict

    :raises ~django.core.exceptions.ValidationError: When no slug is given and there is also no field which can be used
                                                     as fallback (either ``title`` or ``name``).

    :return: An unique slug identifier
    :rtype: str
    """
    slug = kwargs.get("slug")
    foreign_model = kwargs.get("foreign_model")
    object_instance = kwargs.get("object_instance")
    fallback = kwargs.get("fallback")
    cleaned_data = kwargs.get("cleaned_data")
    region = kwargs.get("region")
    language = kwargs.get("language")

    logger.debug("foreign_model: %r", foreign_model)
    if foreign_model in ["page", "event", "poi"]:
        logger.debug("%r, %r", region, language)

    # if slug is empty and fallback field is set, generate from fallback:title/name
    if not slug and fallback:
        if fallback not in cleaned_data:
            raise ValidationError(
                _("Cannot generate slug from %(fallback)s."),
                code="invalid",
                params={"fallback": _(fallback)},
            )
        # Check whether slug field supports unicode
        # pylint: disable=protected-access
        allow_unicode = object_instance._meta.get_field("slug").allow_unicode
        # slugify to make sure slug doesn't contain special chars etc.
        slug = slugify(cleaned_data[fallback], allow_unicode=allow_unicode)
        # If the title/name field didn't contain valid characters for a slug, we use a hardcoded fallback slug
        if not slug:
            slug = foreign_model

    unique_slug = slug
    i = 1
    pre_filtered_objects = kwargs["manager"]

    # if the foreign model is a content type (e.g. page, event or poi), make sure slug is unique per region and language
    if foreign_model in ["page", "event", "poi"]:
        pre_filtered_objects = pre_filtered_objects.filter(
            **{
                foreign_model + "__region": region,
                "language": language,
            }
        )

    # generate new slug while it is not unique
    while True:
        # get other objects with same slug
        other_objects = pre_filtered_objects.filter(slug=unique_slug)
        if object_instance and object_instance.id:
            if foreign_model in ["page", "event", "poi"]:
                # other objects which are just other versions of this object are allowed to have the same slug
                other_objects = other_objects.exclude(
                    **{
                        foreign_model: object_instance.foreign_object,
                        "language": language,
                    }
                )
            else:
                # the current object is also allowed to have the same slug
                other_objects = other_objects.exclude(id=object_instance.id)
        if not other_objects.exists():
            break
        i += 1
        unique_slug = f"{slug}-{i}"

    logger.debug("unique slug: %r", unique_slug)
    return unique_slug
