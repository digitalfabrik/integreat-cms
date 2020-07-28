"""
This module contains helpers regarding unique string identifiers without special characters ("slugs").
"""

import logging

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


def generate_unique_slug(form_object, foreign_model):
    """
    This function can be used in :mod:`~cms.forms` to clean slug fields. It will make sure the slug field contains a
    unique identifier per region and language. It can also be used for region slugs (``foreign_model`` is ``None`` in
    this case). If the slug field is empty, it creates a fallback value from either the ``title`` or the ``name`` field.
    In case the slug exists already, it appends a counter which is increased until the slug is unique.

    Example usages:

    * :func:`cms.forms.regions.region_form.RegionForm.clean_slug`
    * :func:`cms.forms.pages.page_translation_form.PageTranslationForm.clean_slug`
    * :func:`cms.forms.events.event_translation_form.EventTranslationForm.clean_slug`
    * :func:`cms.forms.pois.poi_translation_form.POITranslationForm.clean_slug`

    :param form_object: The form which contains the slug field
    :type form_object: ~django.forms.Form

    :param foreign_model: If the form instance has a foreign key to another model (e.g. because it is a translation of
                          a content-object), this paramaeter contains the model of the foreign related object.
    :type foreign_model: ~django.db.models.Model

    :return: An unique slug identifier
    :rtype: str
    """

    logger.info('generate_unique_slug()')
    logger.info('foreign_model: "%s"', foreign_model)
    if foreign_model in ['page', 'event', 'poi']:
        logger.info('region: "%s"', form_object.region)
        logger.info('language: "%s"', form_object.language)

    slug = form_object.cleaned_data['slug']

    # if slug is empty, generate from title/name
    if not slug:
        # determine fallback field of the model
        if foreign_model in ['page', 'event', 'poi']:
            fallback = 'title'
        else:
            fallback = 'name'
        if fallback not in form_object.cleaned_data:
            raise ValidationError(
                _('Cannot generate slug from %(fallback)s.'),
                code='invalid',
                params={'fallback': fallback}
            )
        # slugify to make sure slug doesn't contain special chars etc.
        slug = slugify(form_object.cleaned_data[fallback], allow_unicode=True)
        # If the title/name field didn't contain valid characters for a slug, we use a hardcoded fallback slug
        if not slug:
            slug = foreign_model

    unique_slug = slug
    i = 1
    pre_filtered_objects = form_object.Meta.model.objects

    # if the foreign model is a content type (e.g. page, event or poi), make sure slug is unique per region and language
    if foreign_model in ['page', 'event', 'poi']:
        pre_filtered_objects = pre_filtered_objects.filter(**{
            foreign_model + '__region': form_object.region,
            'language': form_object.language
        })

    # generate new slug while it is not unique
    while True:
        # get other objects with same slug
        other_objects = pre_filtered_objects.filter(slug=unique_slug)
        if form_object.instance.id:
            if foreign_model in ['page', 'event', 'poi']:
                # other objects which are just other versions of this object are allowed to have the same slug
                other_objects = other_objects.exclude(**{
                    foreign_model: form_object.instance.foreign_object,
                    'language': form_object.language
                })
            else:
                # the current object is also allowed to have the same slug
                other_objects = other_objects.exclude(id=form_object.instance.id)
        if not other_objects.exists():
            break
        i += 1
        unique_slug = f'{slug}-{i}'

    logger.info('unique slug: %s', unique_slug)
    return unique_slug
