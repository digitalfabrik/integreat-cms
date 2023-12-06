from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.core.exceptions import ValidationError

from integreat_cms.cms.models import PageTranslation, Region
from integreat_cms.cms.utils.slug_utils import generate_unique_slug

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper

    from integreat_cms.cms.utils.slug_utils import SlugKwargs


@pytest.mark.django_db
def test_generate_unique_slug_fallback(
    settings: SettingsWrapper, load_test_data: None
) -> None:
    """
    Test whether the :meth:`~integreat_cms.cms.utils.slug_utils.generate_unique_slug_helper` function correctly uses the fallback property
    when no slug is provided
    """
    region = Region.objects.get(slug="augsburg")
    kwargs: SlugKwargs = {
        "cleaned_data": {"name": "unique_slug_fallback"},
        "manager": Region.objects,
        "object_instance": region,
        "foreign_model": "region",
        "fallback": "name",
    }
    assert (
        generate_unique_slug(**kwargs) == "unique_slug_fallback"
    ), "Name is not used as fallback when slug is missing"


@pytest.mark.django_db
def test_generate_unique_slug_reserved_region_slug(
    settings: SettingsWrapper, load_test_data: None
) -> None:
    """
    Test whether the :meth:`~integreat_cms.cms.utils.slug_utils.generate_unique_slug_helper` function returns the correct unique slug
    when the new region slug is a reserved slug
    """
    region = Region.objects.get(slug="augsburg")
    kwargs: SlugKwargs = {
        "slug": "landing",
        "cleaned_data": {},
        "manager": Region.objects,
        "object_instance": region,
        "foreign_model": "region",
        "fallback": "name",
    }
    assert (
        generate_unique_slug(**kwargs) == "landing-2"
    ), "Reserved region slug is not prevented"


@pytest.mark.django_db
def test_generate_unique_slug_reserved_page_slug(
    settings: SettingsWrapper, load_test_data: None
) -> None:
    """
    Test whether the :meth:`~integreat_cms.cms.utils.slug_utils.generate_unique_slug_helper` function  function returns the correct unique slug
    when the new page slug is a reserved slug
    """
    page = PageTranslation.objects.filter(page__region__slug="augsburg").first()
    kwargs: SlugKwargs = {
        "slug": "disclaimer",
        "cleaned_data": {},
        "manager": PageTranslation.objects,
        "language": page.language,
        "object_instance": page,
        "foreign_model": "page",
    }
    assert (
        generate_unique_slug(**kwargs) == "disclaimer-2"
    ), "Reserved imprint slug is not prevented for pages"


def test_generate_unique_slug_no_fallback() -> None:
    """
    Test whether the :meth:`~integreat_cms.cms.utils.slug_utils.generate_unique_slug_helper` throws a :class:`django.core.exceptions.ValidationError`,
    while the fallback property does not exist
    """
    kwargs: SlugKwargs = {
        "cleaned_data": {},
        "manager": [],
        "object_instance": Region(),
        "foreign_model": "region",
        "fallback": "name",
    }
    with pytest.raises(ValidationError):
        generate_unique_slug(**kwargs)
