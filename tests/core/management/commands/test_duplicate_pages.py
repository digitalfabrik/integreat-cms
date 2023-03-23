import pytest
from django.core.management.base import CommandError

from integreat_cms.cms.models import Page, PageTranslation

from ..utils import get_command_output


def test_duplicate_pages_prod():
    """
    Ensure that this command does not work in production mode
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("duplicate_pages", "region_slug"))
    assert str(exc_info.value) == "This command can only be used in DEBUG mode."


def test_duplicate_pages_missing_region_slug(settings):
    """
    Ensure that a missing region slug throws an error
    """
    settings.DEBUG = True
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("duplicate_pages"))
    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: region_slug"
    )


@pytest.mark.django_db
def test_duplicate_pages_non_existing_region(settings):
    """
    Ensure that a non existing region slug throws an error
    """
    settings.DEBUG = True
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("duplicate_pages", "non-existing"))
    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


# pylint: disable=unused-argument
@pytest.mark.django_db
def test_duplicate_pages(settings, load_test_data):
    """
    Ensure that pages are really duplicated
    """
    settings.DEBUG = True
    region_slug = "augsburg"
    page_count_before = Page.objects.filter(region__slug=region_slug).count()
    translations_count_before = PageTranslation.objects.filter(
        page__region__slug=region_slug
    ).count()
    out, err = get_command_output("duplicate_pages", "augsburg")
    assert '✔ Successfully duplicated pages for region "Stadt Augsburg".' in out
    assert not err
    page_count_after = Page.objects.filter(region__slug=region_slug).count()
    translations_count_after = PageTranslation.objects.filter(
        page__region__slug=region_slug
    ).count()
    assert (
        page_count_after == 2 * page_count_before
    ), "The count of pages should have doubled after the command"
    assert (
        translations_count_after == 2 * translations_count_before
    ), "The count of page translations should have doubled after the command"
