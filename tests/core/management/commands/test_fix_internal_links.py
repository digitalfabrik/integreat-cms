import pytest
from django.core.management.base import CommandError
from linkcheck.listeners import enable_listeners
from linkcheck.models import Link, Url

from ..utils import get_command_output


@pytest.mark.django_db
def test_fix_internal_links_non_existing_region(load_test_data):
    """
    Ensure that a non existing region slug throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output("fix_internal_links", "--region-slug=non-existing")
        )
    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_fix_internal_links_non_existing_username(load_test_data):
    """
    Ensure that a non existing username throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output("fix_internal_links", "--username=non-existing")
        )
    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_fix_internal_links_dry_run(load_test_data_transactional):
    """
    Ensure that dry run works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :type load_test_data_transactional: tuple
    """
    old_url = "https://integreat.app/augsburg/de/deutsche-sprache/sprachlernangebote/"
    new_url = "https://integreat.app/augsburg/de/deutsche-sprache/sonstige-sprachlernangebote/"

    assert Url.objects.filter(url=old_url).exists()
    assert Link.objects.filter(url__url=old_url).count() == 1

    assert not Url.objects.filter(url=new_url).exists()
    assert not Link.objects.filter(url__url=new_url).exists()

    with enable_listeners():
        out, err = get_command_output("fix_internal_links")
    assert "✔ Finished dry-run of fixing broken internal links." in out
    assert not err

    assert Url.objects.filter(
        url=old_url
    ).exists(), "Old URL should not be removed during dry run"
    assert (
        Link.objects.filter(url__url=old_url).count() == 1
    ), "Old link should not be removed during dry run"

    assert not Url.objects.filter(
        url=new_url
    ).exists(), "New URL should not be created during dry run"
    assert not Link.objects.filter(
        url__url=new_url
    ).exists(), "New link should not be created during dry run"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_fix_internal_links_commit(load_test_data_transactional):
    """
    Ensure that committing changes to the database works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :type load_test_data_transactional: tuple
    """
    old_url = "https://integreat.app/augsburg/de/deutsche-sprache/sprachlernangebote/"
    new_url = "https://integreat.app/augsburg/de/deutsche-sprache/sonstige-sprachlernangebote/"

    assert Url.objects.filter(url=old_url).exists()
    assert Link.objects.filter(url__url=old_url).count() == 1

    assert not Url.objects.filter(url=new_url).exists()
    assert not Link.objects.filter(url__url=new_url).exists()

    # Now pass --commit to write changes to database
    with enable_listeners():
        out, err = get_command_output("fix_internal_links", "--commit")
    assert "✔ Successfully finished fixing broken internal links." in out
    assert not err

    assert not Url.objects.filter(
        url=old_url
    ).exists(), "Old URL should not exist after replacement"
    assert not Link.objects.filter(
        url__url=old_url
    ).exists(), "Old link should not exist after replacement"

    assert Url.objects.filter(
        url=new_url
    ).exists(), "New URL should exist after replacement"
    assert (
        Link.objects.filter(url__url=new_url).count() == 1
    ), "New link should exist after replacement"
