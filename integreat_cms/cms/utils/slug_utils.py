"""
This module contains helpers regarding unique string identifiers without special characters ("slugs").
"""

from __future__ import annotations

import logging
from time import time
from typing import Final, Literal, TYPE_CHECKING

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from typing import (
        Any,
        NotRequired,
        TypeAlias,
        TypedDict,
        TypeVar,
        Unpack,
    )

    from django.db.models import Manager, QuerySet
    from django.forms import ModelForm
    from django.http.request import QueryDict

    from ..models import Language, Region
    from ..models.abstract_base_model import AbstractBaseModel
    from ..models.abstract_content_model import AbstractContentModel

    T = TypeVar("T")

SlugObject = Literal["page", "event", "poi"]
DEFAULT_OBJECTS: Final[tuple[SlugObject, ...]] = ("event", "poi", "page")
ALLOWED_OBJECTS = {"event", "poi", "page"}


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    ForeignModelType: TypeAlias = Literal[
        "page",
        "event",
        "poi",
        "region",
        "organization",
        "offer-template",
    ]

    class SlugKwargs(TypedDict):
        """
        A custom type for keyword arguments to :func:`generate_unique_slug`
        """

        cleaned_data: NotRequired[QueryDict]
        fallback: NotRequired[Literal["name", "title"]]
        foreign_model: ForeignModelType
        foreign_object: NotRequired[AbstractContentModel]
        language: NotRequired[Language]
        manager: Manager
        object_instance: AbstractBaseModel
        region: NotRequired[Region]
        slug: NotRequired[str]


def generate_unique_slug_helper(
    form_object: ModelForm,
    foreign_model: ForeignModelType,
) -> str:
    """
    This function acts like an interface and extracts all parameters of the form_object before actually generating
    the unique slug, so that unique slug generation can be performed without any cleaned form data after a form submission.

    :param form_object: The form which contains the slug field
    :param foreign_model: If the form instance has a foreign key to another model (e.g. because it is a translation of
                          a content-object), this parameter contains the model of the foreign related object.
    :raises ~django.core.exceptions.ValidationError: When no slug is given and there is also no field which can be used
                                                     as fallback (either ``title`` or ``name``).

    :return: An unique slug identifier
    """
    kwargs: SlugKwargs = {
        "slug": form_object.cleaned_data["slug"],
        "cleaned_data": form_object.cleaned_data,
        "manager": form_object.Meta.model.objects,
        "object_instance": form_object.instance,
        "foreign_model": foreign_model,
        "fallback": "name",
    }
    if foreign_model in ALLOWED_OBJECTS:
        kwargs.update(
            {
                "region": form_object.instance.foreign_object.region,
                "language": form_object.instance.language,
                "fallback": "title",
            },
        )
    return generate_unique_slug(**kwargs)


def generate_unique_slug(**kwargs: Unpack[SlugKwargs]) -> str:
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
    :raises ~django.core.exceptions.ValidationError: When no slug is given and there is also no field which can be used
                                                     as fallback (either ``title`` or ``name``).

    :return: An unique slug identifier
    """
    slug: str = kwargs.get("slug", "")
    foreign_model: str | None = kwargs.get("foreign_model")
    foreign_object: AbstractContentModel | None = kwargs.get("foreign_object")
    object_instance: AbstractBaseModel = kwargs["object_instance"]
    fallback: Literal["name", "title", ""] = kwargs.get("fallback", "")
    cleaned_data: dict[str, Any] = kwargs.get("cleaned_data", {})
    region: Region | None = kwargs.get("region")
    language: Language | None = kwargs.get("language")
    manager: Any = kwargs["manager"]

    logger.debug("foreign_model: %r", foreign_model)
    if foreign_model in ALLOWED_OBJECTS:
        logger.debug("%r, %r", region, language)
    logger.debug("slug: %r", slug)

    base_slug = generate_base_slug(
        slug, fallback, cleaned_data, object_instance, foreign_model
    )
    pre_filtered_objects = get_prefiltered_queryset(
        manager,
        foreign_model,
        region,
        language,
    )

    unique_slug = base_slug
    counter = 1

    while True:
        other_objects = pre_filtered_objects.filter(slug=unique_slug)

        if object_instance:
            other_objects = exclude_current_object(
                other_objects,
                object_instance,
                foreign_model,
                foreign_object,
            )

        if not other_objects.exists() and not is_reserved_slug(
            unique_slug, foreign_model
        ):
            break

        counter += 1
        unique_slug = f"{base_slug}-{counter}"

    logger.debug("unique slug: %r", unique_slug)
    return unique_slug


def generate_base_slug(
    slug: str,
    fallback: str,
    cleaned_data: dict[str, Any],
    object_instance: AbstractBaseModel,
    foreign_model: str | None,
) -> str:
    """
    Generates the base slug either from the given slug or from the fallback field.
    """
    if slug:
        return slug

    if fallback not in cleaned_data:
        raise ValidationError(
            _("Cannot generate slug from {}.").format(_(fallback)),
            code="invalid",
        )

    allow_unicode = object_instance._meta.get_field("slug").allow_unicode
    slug = slugify(cleaned_data[fallback], allow_unicode=allow_unicode)

    return slug or foreign_model or ""


def get_prefiltered_queryset(
    manager: Any,
    foreign_model: str | None,
    region: Region | None,
    language: Language | None,
) -> Any:
    """
    Returns a prefiltered queryset depending on the foreign model, region and language.
    """
    if foreign_model in ALLOWED_OBJECTS:
        return manager.filter(
            **{
                foreign_model + "__region": region,
                "language": language,
            }
        )
    return manager


def is_reserved_slug(slug: str | None, foreign_model: str | None) -> bool:
    """
    Checks whether the given slug is reserved for the given foreign model.
    """
    if foreign_model == "page":
        return slug in settings.RESERVED_REGION_PAGE_PATTERNS
    if foreign_model == "region":
        return slug in settings.RESERVED_REGION_SLUGS
    return False


def exclude_current_object(
    qs: QuerySet[T],
    object_instance: AbstractBaseModel,
    foreign_model: str | None,
    foreign_object: AbstractContentModel | None,
) -> QuerySet[T]:
    """
    Excludes the current object from the given queryset to avoid false positives when checking for slug uniqueness.
    When the foreign object doesn't exist in the DB yet (no ID), we skip exclusion since there's nothing to exclude.
    """
    if not object_instance:
        return qs

    if (
        foreign_model in ALLOWED_OBJECTS
        and (foreign_object or object_instance.foreign_object).id
    ):
        return qs.exclude(
            **{foreign_model: foreign_object or object_instance.foreign_object}
        )

    if object_instance.id:
        return qs.exclude(id=object_instance.id)

    return qs


def update_translations(
    translations: QuerySet, foreign_attr: Literal["page", "event", "poi"], dry_run: bool
) -> int:
    logger.info("Updating slugs in %sTranslations", foreign_attr.capitalize())
    counter = 0
    with transaction.atomic():
        for translation in translations:
            foreign_obj: AbstractContentModel | None = getattr(
                translation, foreign_attr, None
            )
            if foreign_obj is None:
                continue
            region = getattr(foreign_obj, "region", None)
            if not region:
                continue
            old_slug = translation.slug
            translation.slug = generate_unique_slug(
                slug=translation.slug,
                manager=type(translation).objects,
                object_instance=translation,
                foreign_model=foreign_attr,
                foreign_object=foreign_obj,
                region=region,
                language=translation.language,
            )
            if old_slug != translation.slug:
                counter += 1
                if not dry_run:
                    translation.save()
    return counter


@shared_task()
def make_all_slugs_unique(
    objects: tuple[SlugObject, ...] = DEFAULT_OBJECTS,
    dry_run: bool = False,
) -> None:
    logger.info("Starting to make all slugs unique ...")
    start_time = time()

    slug_counter = 0

    for model_name in objects:
        translation_model = apps.get_model(
            "cms", f"{model_name.capitalize()}Translation"
        )
        translations = translation_model.objects.all()
        slug_counter += update_translations(translations, model_name, dry_run)

    end_time = time() - start_time
    if not dry_run:
        logger.info(
            "Finished >make_all_slugs_unique< after: %.3fs with %d updated slugs",
            end_time,
            slug_counter,
        )
    if dry_run:
        logger.info(
            "Finished dry run for >make_all_slugs_unique< after: %.3fs. "
            "In total %d non-unique slugs were identified. "
            "Keep in mind that during a real run, "
            "only a subset of the non-unique slugs will be actually changed in order to make them all unique.",
            end_time,
            slug_counter,
        )
