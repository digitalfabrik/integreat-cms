from collections.abc import Callable
from datetime import timedelta

import pytest
from django.utils import timezone

from integreat_cms.cms.models import Language, PageTranslation, Region
from integreat_cms.cms.models.pages.page import Page


@pytest.mark.django_db
def test_when_creating_page_translations_to_automatically_create_unique_slugs(
    create_page: Callable[..., Page],
) -> None:
    region = Region.objects.create(name="new-region")

    page1 = create_page(region=region)
    page2 = create_page(region=region)
    language = Language.objects.create(slug="da", primary_country_code="de")

    page_translation1 = PageTranslation.objects.create(
        page=page1, language=language, slug="new-slug"
    )
    page_translation2 = PageTranslation.objects.create(
        page=page2, language=language, slug="new-slug"
    )

    assert page_translation1.slug != page_translation2.slug


@pytest.mark.django_db
def test_get_translatable_attributes_content_and_title_changed(
    create_page: Callable[..., Page], create_language: Callable[..., Language]
) -> None:
    region = Region.objects.create(name="new-region")

    page = create_page(region=region)
    language1 = create_language(slug="aaa", bcp47_tag="aaa")
    language2 = create_language(slug="bbb", bcp47_tag="bbb")

    PageTranslation.objects.create(
        page=page,
        language=language1,
        slug="new-slug",
        title="First Title",
        content="First Content",
        version=1,
        last_updated=timezone.now() - timedelta(seconds=2),
    )
    PageTranslation.objects.create(
        page=page,
        language=language2,
        slug="new-slug",
        title="First Title",
        content="First Content",
        version=1,
        last_updated=timezone.now() - timedelta(seconds=1),
    )
    PageTranslation.objects.create(
        page=page,
        language=language1,
        slug="new-slug",
        title="Second Title",
        content="Second Content",
        version=2,
        last_updated=timezone.now(),
    )

    attrs = ["title", "content"]

    translatable_attributes = page.get_translatable_attributes(
        attrs=attrs, source_language_slug="aaa", target_language_slug="bbb"
    )

    attr_names = [name for name, _ in translatable_attributes]

    assert "title" in attr_names
    assert "content" in attr_names


@pytest.mark.django_db
def test_get_translatable_attributes_content_only_changed(
    create_page: Callable[..., Page], create_language: Callable[..., Language]
) -> None:
    region = Region.objects.create(name="new-region")

    page = create_page(region=region)
    language1 = create_language(slug="aaa", bcp47_tag="aaa")
    language2 = create_language(slug="bbb", bcp47_tag="bbb")

    PageTranslation.objects.create(
        page=page,
        language=language1,
        slug="new-slug",
        title="First Title",
        content="First Content",
        version=1,
        last_updated=timezone.now() - timedelta(seconds=2),
    )
    PageTranslation.objects.create(
        page=page,
        language=language2,
        slug="new-slug",
        title="First Title",
        content="First Content",
        version=1,
        last_updated=timezone.now() - timedelta(seconds=1),
    )
    PageTranslation.objects.create(
        page=page,
        language=language1,
        slug="new-slug",
        title="First Title",
        content="Second Content",
        version=2,
        last_updated=timezone.now(),
    )

    attrs = ["title", "content"]

    translatable_attributes = page.get_translatable_attributes(
        attrs=attrs, source_language_slug="aaa", target_language_slug="bbb"
    )

    attr_names = [name for name, _ in translatable_attributes]

    assert "title" not in attr_names
    assert "content" in attr_names


@pytest.mark.django_db
def test_get_translatable_attributes_first_translation(
    create_page: Callable[..., Page], create_language: Callable[..., Language]
) -> None:
    region = Region.objects.create(name="new-region")

    page = create_page(region=region)
    language1 = create_language(slug="aaa", bcp47_tag="aaa")
    language2 = create_language(slug="bbb", bcp47_tag="bbb")

    PageTranslation.objects.create(
        page=page,
        language=language2,
        slug="new-slug",
        title="First Title",
        content="First Content",
        last_updated=timezone.now() - timedelta(seconds=1),
    )
    PageTranslation.objects.create(
        page=page,
        language=language1,
        slug="new-slug",
        title="First Title",
        content="Second Content",
        last_updated=timezone.now(),
    )

    attrs = ["title", "content"]

    translatable_attributes = page.get_translatable_attributes(
        attrs=attrs, source_language_slug="aaa", target_language_slug="bbb"
    )

    attr_names = [name for name, _ in translatable_attributes]

    assert "title" in attr_names
    assert "content" in attr_names
