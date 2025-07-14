import pytest

from integreat_cms.cms.models import Language, Page, PageTranslation, Region


@pytest.mark.django_db
def test_when_creating_page_translations_to_automatically_create_unique_slugs() -> None:
    region = Region.objects.create(name="new-region")

    page1 = Page.objects.create(
        region=region,
        lft=1,
        rgt=2,
        tree_id=14,
        depth=1,
    )
    page2 = Page.objects.create(
        region=region,
        lft=1,
        rgt=2,
        tree_id=15,
        depth=1,
    )
    language = Language.objects.create(
        slug="da", primary_country_code="de"
    )

    page_translation1 = PageTranslation.objects.create(
        page=page1, language=language, slug="new-slug"
    )
    page_translation2 = PageTranslation.objects.create(
        page=page2, language=language, slug="new-slug"
    )

    assert page_translation1.slug != page_translation2.slug
