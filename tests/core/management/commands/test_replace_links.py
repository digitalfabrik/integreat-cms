import pytest
from django.core.management.base import CommandError
from linkcheck.listeners import enable_listeners
from linkcheck.models import Link, Url

from ..utils import get_command_output


def test_replace_links_missing_args():
    """
    Ensure that missing args cause an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("replace_links"))
    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: search, replace"
    )


def test_replace_links_missing_replace():
    """
    Ensure that a missing replace throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("replace_links", "search"))
    assert str(exc_info.value) == "Error: the following arguments are required: replace"


@pytest.mark.django_db
def test_replace_links_non_existing_region(load_test_data):
    """
    Ensure that a non existing region slug throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output(
                "replace_links", "replace_links", "search", "--region-slug=non-existing"
            )
        )
    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_replace_links_non_existing_username(load_test_data):
    """
    Ensure that a non existing username throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output(
                "replace_links", "replace_links", "search", "--username=non-existing"
            )
        )
    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_replace_links_dry_run(load_test_data_transactional):
    """
    Ensure that dry run works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :type load_test_data_transactional: tuple
    """
    test_url = "https://integreat.app/augsburg/de/willkommen/"
    search = "/augsburg/"
    replace = "/new-slug/"
    replaced_url = test_url.replace(search, replace)
    assert Url.objects.filter(
        url=test_url
    ).exists(), "Test URL should exist in test data"
    assert (
        Link.objects.filter(url__url=test_url).count() == 3
    ), "Test link should exist in test data"
    assert not Url.objects.filter(
        url=replaced_url
    ).exists(), "Replaced URL should not exist in test data"
    assert not Link.objects.filter(
        url__url=replaced_url
    ).exists(), "Replaced link should not exist in test data"
    # Test dry run without --commit
    with enable_listeners():
        out, err = get_command_output("replace_links", search, replace)
    assert (
        f'✔ Finished dry-run of replacing "{search}" with "{replace}" in content links.'
        in out
    )
    assert not err
    assert Url.objects.filter(
        url=test_url
    ).exists(), "Test URL should not be removed during dry run"
    assert (
        Link.objects.filter(url__url=test_url).count() == 3
    ), "Test link should not be removed during dry run"
    assert not Url.objects.filter(
        url=replaced_url
    ).exists(), "Replaced URL should not be created during dry run"
    assert not Link.objects.filter(
        url__url=replaced_url
    ).exists(), "Replaced link should not be created during dry run"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_replace_links_commit(load_test_data_transactional):
    """
    Ensure that committing changes to the database works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :type load_test_data_transactional: tuple
    """
    test_url = "https://integreat.app/augsburg/de/willkommen/"
    search = "/augsburg/"
    replace = "/new-slug/"
    replaced_url = test_url.replace(search, replace)
    assert Url.objects.filter(
        url=test_url
    ).exists(), "Test URL should not be removed during dry run"
    assert (
        Link.objects.filter(url__url=test_url).count() == 3
    ), "Test link should not be removed during dry run"
    assert not Url.objects.filter(
        url=replaced_url
    ).exists(), "Replaced URL should not be created during dry run"
    assert not Link.objects.filter(
        url__url=replaced_url
    ).exists(), "Replaced link should not be created during dry run"
    # Now pass --commit to write changes to database
    with enable_listeners():
        out, err = get_command_output("replace_links", search, replace, "--commit")
    assert (
        f'✔ Successfully replaced "{search}" with "{replace}" in content links.' in out
    )
    assert not err
    assert not Url.objects.filter(
        url=test_url
    ).exists(), "Test URL should not exist after replacement"
    assert not Link.objects.filter(
        url__url=test_url
    ).exists(), "Test link should not exist after replacement"
    assert Url.objects.filter(
        url=replaced_url
    ).exists(), "Replaced URL should exist after replacement"
    assert (
        Link.objects.filter(url__url=replaced_url).count() == 3
    ), "Replaced link should exist after replacement"
