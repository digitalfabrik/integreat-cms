from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


import pytest
from django.core.management.base import CommandError
from linkcheck.listeners import enable_listeners
from linkcheck.models import Link, Url

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Organization, PageTranslation

from ..utils import get_command_output


@pytest.mark.django_db
def test_fix_internal_links_non_existing_region(load_test_data: None) -> None:
    """
    Ensure that a non existing region slug throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output("fix_internal_links", "--region-slug=non-existing"),
        )
    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_fix_internal_links_non_existing_username(
    load_test_data: None,
) -> None:
    """
    Ensure that a non existing username throws an error

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(
            get_command_output("fix_internal_links", "--username=non-existing"),
        )
    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'


@pytest.mark.django_db
def test_fix_internal_links_skips_links_without_public_target_translation(
    load_test_data: None,
) -> None:
    """
    Ensure that a link whose target has no public translation in the language of the
    linking content is skipped instead of crashing the command

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    # The English translation of the "test-links" page links to the German page
    # "willkommen". Unpublish the English translation of that page, so that no
    # public link target exists in the language of the linking content.
    PageTranslation.objects.filter(page__id=1, language__slug="en").update(
        status=status.DRAFT,
    )

    with enable_listeners():
        out, err = get_command_output("fix_internal_links")

    assert "✔ Finished dry-run of fixing broken internal links." in out
    assert not err


@pytest.mark.django_db
def test_fix_internal_links_skips_organization_links(load_test_data: None) -> None:
    """
    Ensure that links of organizations (which have no language and no versioning)
    are skipped instead of crashing the command

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    internal_url = "https://integreat.app/augsburg/de/willkommen/"
    organization = Organization.objects.get(id=1)
    Organization.objects.filter(id=organization.id).update(website=internal_url)
    Link.objects.create(
        url=Url.objects.get(url=internal_url),
        content_object=organization,
        field="website",
        text=organization.name,
    )

    with enable_listeners():
        out, err = get_command_output("fix_internal_links")

    assert "✔ Finished dry-run of fixing broken internal links." in out
    assert not err
    assert Link.objects.filter(
        organization__id=organization.id,
    ).exists(), "The organization link should not be modified"


old_urls = [
    "https://integreat.app/augsburg/de/willkommen/",
    "https://integreat.app/augsburg/de/events/test-veranstaltung/",
    "https://integreat.app/augsburg/de/locations/test-ort/",
    "http://localhost:8000/s/p/94/",
]

new_urls = [
    "https://integreat.app/augsburg/en/welcome/",
    "https://integreat.app/augsburg/en/events/test-event/",
    "https://integreat.app/augsburg/en/locations/test-location/",
    "https://integreat.app/augsburg/de/test-links/",
]

# A link to a page's outdated (renamed) slug, in the same language as the page itself.
# Historical slug matching was intentionally removed (see #4524, cross-language slug
# matching returned the wrong page), so such links can no longer be resolved and must
# be left untouched instead of being rewritten to the page's current slug.
outdated_slug_url = (
    "https://integreat.app/augsburg/de/deutsche-sprache/sprachlernangebote/"
)
renamed_slug_url = (
    "https://integreat.app/augsburg/de/deutsche-sprache/sonstige-sprachlernangebote/"
)


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_fix_internal_links_dry_run(
    load_test_data_transactional: Any | None,
) -> None:
    """
    Ensure that dry run works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    """
    old_link_occurrence_counts = []

    for old_url in old_urls:
        assert Url.objects.filter(url=old_url).exists()
        assert Link.objects.filter(url__url=old_url).exists()
        old_link_occurrence_counts.append(Link.objects.filter(url__url=old_url).count())

    for new_url in new_urls:
        assert not Url.objects.filter(url=new_url).exists()
        assert not Link.objects.filter(url__url=new_url).exists()

    with enable_listeners():
        out, err = get_command_output("fix_internal_links")
    assert "✔ Finished dry-run of fixing broken internal links." in out
    assert not err

    for link_occurences, old_url in zip(
        old_link_occurrence_counts,
        old_urls,
        strict=False,
    ):
        assert Url.objects.filter(
            url=old_url,
        ).exists(), "Old URL should not be removed during dry run"
        assert Link.objects.filter(url__url=old_url).count() == link_occurences, (
            "Old link should not be modified during dry run"
        )

    for new_url in new_urls:
        assert not Url.objects.filter(
            url=new_url,
        ).exists(), "New URL should not be created during dry run"
        assert not Link.objects.filter(
            url__url=new_url,
        ).exists(), "New link should not be created during dry run"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_fix_internal_links_commit(load_test_data_transactional: Any | None) -> None:
    """
    Ensure that committing changes to the database works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    """
    old_link_occurrence_counts = []

    for old_url in old_urls:
        assert Url.objects.filter(url=old_url).exists()
        assert Link.objects.filter(url__url=old_url).exists()
        old_link_occurrence_counts.append(Link.objects.filter(url__url=old_url).count())

    for new_url in new_urls:
        assert not Url.objects.filter(url=new_url).exists()
        assert not Link.objects.filter(url__url=new_url).exists()

    outdated_slug_link_count = Link.objects.filter(url__url=outdated_slug_url).count()
    assert outdated_slug_link_count > 0
    assert not Url.objects.filter(url=renamed_slug_url).exists()

    # Now pass --commit to write changes to database
    with enable_listeners():
        out, err = get_command_output("fix_internal_links", "--commit")
    assert "✔ Successfully finished fixing broken internal links." in out
    assert not err

    for link_occurrences, old_url in zip(
        old_link_occurrence_counts,
        old_urls,
        strict=False,
    ):
        assert Link.objects.filter(url__url=old_url).count() < link_occurrences, (
            "Some old links should not exist after replacement"
        )

    for new_url in new_urls:
        assert Url.objects.filter(
            url=new_url,
        ).exists(), "New URL should exist after replacement"
        assert Link.objects.filter(url__url=new_url).count() == 1, (
            "New link should exist after replacement"
        )

    # A link to a renamed slug in the same language cannot be resolved anymore and
    # must be left untouched, since historical slug matching is no longer supported
    assert (
        Link.objects.filter(url__url=outdated_slug_url).count()
        == outdated_slug_link_count
    ), "Links to an outdated slug should not be modified"
    assert not Url.objects.filter(
        url=renamed_slug_url,
    ).exists(), "The renamed slug's URL should not be created"


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True)
def test_fix_internal_links_commit_skips_version_conflicts(
    load_test_data_transactional: Any | None,
) -> None:
    """
    Ensure that a version number conflict (e.g. because an editor saved a new version
    while the command was running) only skips the affected translation instead of
    aborting the whole command and losing its link records

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    """
    # Simulate a concurrent editor save: the latest version in the database is newer
    # than the version the linkcheck data still points to. The English translation of
    # the "test-links" page is the one whose links to the German page "willkommen",
    # the event "test-veranstaltung" and the location "test-ort" would be fixed.
    stale_translation = PageTranslation.objects.get(
        page__id=27,
        language__slug="en",
        version=1,
    )
    newer_version = stale_translation.create_new_version_copy()
    newer_version.save()

    stale_link_count = stale_translation.links.count()
    assert stale_link_count > 0

    # The URL that only the conflicting translation would produce
    skipped_url = "https://integreat.app/augsburg/en/welcome/"
    # URLs that fixes of other translations produce
    fixed_urls = [
        "https://integreat.app/augsburg/de/test-links/",
    ]
    for url in [skipped_url, *fixed_urls]:
        assert not Url.objects.filter(
            url=url,
        ).exists(), "The fixed URL should not exist before the command is run"

    with enable_listeners():
        out, err = get_command_output("fix_internal_links", "--commit")

    assert "✔ Successfully finished fixing broken internal links." in out
    assert "newer version" in err, (
        "The skipped version conflict should be reported as a warning"
    )

    # The conflicting translation must be skipped and keep its link records
    assert stale_translation.links.count() == stale_link_count, (
        "The link records of the skipped translation should be preserved"
    )
    # The command must not have written its stale copy on top of the concurrently
    # created version. Asserted directly on the version rows, because the URL check
    # below only observes the symptom and would also trip on link records that
    # unrelated test pollution attached to another version of this translation.
    assert not PageTranslation.objects.filter(
        page=stale_translation.page,
        language=stale_translation.language,
        version__gt=newer_version.version,
    ).exists(), "No version newer than the concurrently created one should exist"
    assert not Url.objects.filter(
        url=skipped_url,
    ).exists(), "The links of the conflicting translation should not be replaced"

    # All other translations must still be fixed
    for url in fixed_urls:
        assert Link.objects.filter(url__url=url).count() == 1, (
            "Links in other translations should still be replaced"
        )
