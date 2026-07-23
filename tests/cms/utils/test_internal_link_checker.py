from __future__ import annotations

import pytest
from linkcheck.models import Url

from integreat_cms.cms.utils.internal_link_checker import check_internal

VALID_INTERNAL_LINKS: list[str] = [
    "https://integreat.app",
    "https://integreat.app/augsburg",
    "https://integreat.app/augsburg/de",
    "https://integreat.app/augsburg/en",
    "https://integreat.app/augsburg/de/disclaimer",
    "https://integreat.app/augsburg/ar/disclaimer",
    "https://integreat.app/augsburg/de/events",
    "https://integreat.app/augsburg/de/events/test-veranstaltung",
    "https://integreat.app/augsburg/ar/events/test-veranstaltung",
    "https://integreat.app/augsburg/de/locations",
    "https://integreat.app/augsburg/de/locations/test-ort",
    "https://integreat.app/augsburg/fa/locations/test-ort",
    "https://integreat.app/augsburg/de/news/local",
    "https://integreat.app/augsburg/de/news/local/1",
    "https://integreat.app/augsburg/de/news/tu-news",
    "https://integreat.app/augsburg/de/offers/sprungbrett",
    "https://integreat.app/augsburg/de/offers/lehrstellen-radar",
    "https://integreat.app/nurnberg/de/offers/ihk-praktikumsboerse",
    "https://integreat.app/augsburg/de/willkommen/uber-die-app-integreat-augsburg",
    "https://integreat.app/augsburg/en/welcome/about-the-integreat-app-augsburg",
    "https://integreat.app/augsburg/ar/%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D9%88%D8%B5%D9%88%D9%84/%D9%85%D8%B1%D8%AD%D8%A8%D8%A7-%D8%A8%D9%83%D9%85-%D9%81%D9%8A-%D9%85%D8%AF%D9%8A%D9%86%D8%A9-%D8%A3%D9%88%D8%AC%D8%B3%D8%A8%D9%88%D8%B1%D8%AC",
    "https://integreat.app/augsburg/fa/%DA%AF%D8%A7%D9%85-%D9%86%D8%AE%D8%B3%D8%AA/%D9%86%D9%82%D8%B4%D9%87-%D8%B4%D9%87%D8%B1",
    "https://integreat.app/nurnberg/de/events/test-veranstaltung",
    "https://integreat.app/nurnberg/de/locations/test-ort",
]

INVALID_INTERNAL_LINKS: list[str] = [
    "https://integreat.app/non-existing",
    "https://integreat.app/non-existing/de",
    "https://integreat.app/augsburg/non-existing",
    "https://integreat.app/augsburg/de/non-existing",
    "https://integreat.app/augsburg/de/disclaimer/non-existing",
    "https://integreat.app/augsburg/de/events/non-existing/",
    "https://integreat.app/augsburg/de/locations/non-existing",
    "https://integreat.app/augsburg/de/locations/entwurf-ort",
    "https://integreat.app/augsburg/ar/news/local/1",
    "https://integreat.app/nurnberg/de/news",
    "https://integreat.app/nurnberg/ar/news/local/1",
    "https://integreat.app/nurnberg/de/news/local/2",
    "https://integreat.app/nurnberg/de/news/tu-news",
    "https://integreat.app/nurnberg/de/news/tu-news/999",
    "https://integreat.app/augsburg/de/offers/ihk-praktikumsboerse",
    "https://integreat.app/augsburg/de/offers/non-existing",
    "https://integreat.app/nurnberg/de/offers/sprungbrett",
    "https://integreat.app/augsburg/de/non-existing/non-existing",
    "https://integreat.app/augsburg/de/beh%C3%B6rden-und-beratung/beh%C3%B6rden/archiviertes-amt",
    "https://integreat.app/augsburg/de/beh%C3%B6rden-und-beratung/beh%C3%B6rden/archiviertes-amt/nicht-archivierte-details",
    "https://integreat.app/augsburg/hidden/test-hidden-language",
    "https://integreat.app/nurnberg/fa/events/test-veranstaltung",
    "https://integreat.app/nurnberg/ar/locations/test-ort",
]

SKIPPED_INTERNAL_LINKS: list[str] = [
    "https://google.com",
    "#anchor",
    "relative-link",
    "/media/file",
    "mailto:test@integreat-app.de",
    "tel:+123456789",
    "https://integreat.app/augsburg/de/news/tu-news/999",
]


def prepage_url(link: str, trailing_slash: bool) -> Url:
    """
    Make sure a link either has or doesn't have a trailing slash

    :param link: The link
    :param trailing_slash: Whether to ensure the trailing slash
    """
    if trailing_slash and not link.endswith("/"):
        link += "/"
    elif not trailing_slash and link.endswith("/"):
        link = link[:-1]
    url, _ = Url.objects.get_or_create(url=link)
    return url


@pytest.mark.django_db
@pytest.mark.parametrize("link", VALID_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_valid(
    load_test_data: None,
    link: str,
    trailing_slash: bool,
) -> None:
    """
    Check whether the given internal URL is correctly identified as valid link

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert check_internal(url), f"URL '{link}' is not correctly identified as valid"


@pytest.mark.django_db
@pytest.mark.parametrize("link", INVALID_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_invalid(
    load_test_data: None,
    link: str,
    trailing_slash: bool,
) -> None:
    """
    Check whether the given internal URL is correctly identified as invalid link

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert not check_internal(
        url,
    ), f"URL '{link}' is not correctly identified as invalid"


@pytest.mark.django_db
@pytest.mark.parametrize("link", SKIPPED_INTERNAL_LINKS)
@pytest.mark.parametrize("trailing_slash", [True, False])
def test_check_internal_skipped(
    load_test_data: None,
    link: str,
    trailing_slash: bool,
) -> None:
    """
    Check whether the given internal URL is correctly skipped

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param link: The URL to check
    :param trailing_slash: Whether to ensure the trailing slash
    """
    url = prepage_url(link, trailing_slash)
    assert check_internal(url) is None, f"URL '{link}' is not skipped"


@pytest.mark.django_db
def test_preserve_ignored_links_across_form_save_cycle(load_test_data: None) -> None:
    """
    Mirrors what ``CustomContentModelForm.save`` does on every editor
    edit: delete the prior version's Link rows, then save the new
    version. ``preserve_ignored_links`` must carry ``ignore=True`` from
    the old translation's Link onto the new translation's freshly
    reconciled Link of the same URL.
    """
    from django.contrib.contenttypes.models import ContentType
    from linkcheck.models import Link
    from linkcheck.worker_tasks import do_check_instance_links

    from integreat_cms.cms.models import PageTranslation
    from integreat_cms.cms.utils.link_ignore_preservation import (
        preserve_ignored_links,
    )

    embedded_url = "https://this-link-is-not-working.de"
    translation = (
        PageTranslation.objects.filter(
            page__region__slug="augsburg",
            language__slug="de",
        )
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=translation.pk).update(
        content=f'<a href="{embedded_url}">First text</a>',
    )
    translation.refresh_from_db()

    content_type = ContentType.objects.get_for_model(PageTranslation)
    do_check_instance_links(
        PageTranslation,
        translation,
        PageTranslation._linklist,
    )
    Link.objects.filter(
        content_type=content_type,
        object_id=translation.pk,
        url__url=embedded_url,
    ).update(ignore=True)

    # Production-equivalent form save: snapshot via context manager,
    # delete the prior version's Links, save a new version with
    # different link text, then reconcile.
    new_translation = translation.create_new_version_copy(user=None)
    new_translation.is_validated = True
    new_translation.content = f'<a href="{embedded_url}">Second text</a>'
    with preserve_ignored_links(translation):
        translation.links.all().delete()
        new_translation.save()
        do_check_instance_links(
            PageTranslation,
            new_translation,
            PageTranslation._linklist,
        )

    surviving_link = Link.objects.get(
        content_type=content_type,
        object_id=new_translation.pk,
        url__url=embedded_url,
    )
    assert surviving_link.ignore is True, (
        "ignore=True should survive the form's delete+save cycle"
    )


@pytest.mark.django_db
def test_preserve_ignored_links_across_internal_url_rewrite(
    load_test_data: None,
) -> None:
    """
    When ``clean_content`` rewrites an internal href (e.g. an ancestor
    slug changed), reconciliation creates a ``Url`` row at the new path
    distinct from the pre-rewrite row. The whitelist must follow the
    link's *target*, not its URL string.
    """
    from django.contrib.contenttypes.models import ContentType
    from linkcheck.models import Link
    from linkcheck.worker_tasks import do_check_instance_links

    from integreat_cms.cms.models import PageTranslation
    from integreat_cms.cms.utils import internal_link_utils
    from integreat_cms.cms.utils.link_ignore_preservation import (
        preserve_ignored_links,
    )

    old_url = (
        "https://integreat.app/augsburg/de/legacy-prefix/"
        "uber-die-app-integreat-augsburg/"
    )
    new_url = (
        "https://integreat.app/augsburg/de/willkommen/uber-die-app-integreat-augsburg/"
    )
    target_old = internal_link_utils.get_public_translation_for_link(old_url)
    target_new = internal_link_utils.get_public_translation_for_link(new_url)
    assert target_old is not None and target_new is not None
    assert target_old.foreign_object.pk == target_new.foreign_object.pk

    translation = (
        PageTranslation.objects.filter(
            page__region__slug="augsburg",
            language__slug="de",
        )
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=translation.pk).update(
        content=f'<a href="{old_url}">link</a>',
    )
    translation.refresh_from_db()

    content_type = ContentType.objects.get_for_model(PageTranslation)
    do_check_instance_links(
        PageTranslation,
        translation,
        PageTranslation._linklist,
    )
    Link.objects.filter(
        content_type=content_type,
        object_id=translation.pk,
        url__url=old_url,
    ).update(ignore=True)

    new_translation = translation.create_new_version_copy(user=None)
    new_translation.is_validated = True
    new_translation.content = f'<a href="{new_url}">link</a>'
    with preserve_ignored_links(translation):
        translation.links.all().delete()
        new_translation.save()
        do_check_instance_links(
            PageTranslation,
            new_translation,
            PageTranslation._linklist,
        )

    surviving_link = Link.objects.get(
        content_type=content_type,
        object_id=new_translation.pk,
        url__url=new_url,
    )
    assert surviving_link.ignore is True, (
        "ignore=True should follow the link's target across a URL rewrite"
    )


@pytest.mark.django_db
def test_preserve_ignored_links_across_update_links_to(load_test_data: None) -> None:
    """
    ``update_links_to`` bumps the version of every translation whose
    content links to the given translation, deleting and re-creating its
    Link rows in the process. ``ignore=True`` on the referencing
    translation's links must survive this cycle.
    """
    from django.contrib.contenttypes.models import ContentType
    from linkcheck.models import Link
    from linkcheck.worker_tasks import do_check_instance_links

    from integreat_cms.cms.models import PageTranslation
    from integreat_cms.cms.utils import internal_link_utils
    from integreat_cms.cms.utils.content_translation_utils import update_links_to

    # An href whose path is outdated but still resolves to the target page,
    # so that ``clean_content`` rewrites it and ``update_links_to`` saves a
    # new version of the referencing translation
    outdated_url = (
        "https://integreat.app/augsburg/de/legacy-prefix/"
        "uber-die-app-integreat-augsburg/"
    )
    target = internal_link_utils.get_public_translation_for_link(outdated_url)
    assert target is not None

    referencing = (
        PageTranslation.objects.filter(
            page__region__slug="augsburg",
            language__slug="de",
            slug="willkommen",
        )
        .order_by("-version")
        .first()
    )
    assert referencing.foreign_object != target.foreign_object
    PageTranslation.objects.filter(pk=referencing.pk).update(
        content=f'<a href="{outdated_url}">link text</a>',
    )
    referencing.refresh_from_db()

    content_type = ContentType.objects.get_for_model(PageTranslation)
    do_check_instance_links(
        PageTranslation,
        referencing,
        PageTranslation._linklist,
    )
    Link.objects.filter(
        content_type=content_type,
        object_id=referencing.pk,
        url__url=outdated_url,
    ).update(ignore=True)

    update_links_to(target, None)

    new_referencing = referencing.latest_version
    assert new_referencing.pk != referencing.pk, (
        "update_links_to should have saved a new version"
    )
    assert target.full_url in new_referencing.content
    do_check_instance_links(
        PageTranslation,
        new_referencing,
        PageTranslation._linklist,
    )

    surviving_link = Link.objects.get(
        content_type=content_type,
        object_id=new_referencing.pk,
        url__url=target.full_url,
    )
    assert surviving_link.ignore is True, (
        "ignore=True should survive the update_links_to version bump"
    )


@pytest.mark.django_db
def test_ignore_inherited_by_new_content_object_same_region(
    load_test_data: None,
) -> None:
    """
    When a URL has already been marked verified (``ignore=True``) on one
    content object, a *different* content object in the same region that
    later comes to contain the same URL must inherit ``ignore=True`` on
    its freshly created Link. Otherwise the URL re-surfaces in the
    dashboard as unverified, with its source column pointing at the old
    (already-verified) content object instead of the newly added one.
    """
    from django.contrib.contenttypes.models import ContentType
    from linkcheck.models import Link
    from linkcheck.worker_tasks import do_check_instance_links

    from integreat_cms.cms.models import Page, PageTranslation
    from integreat_cms.cms.utils.link_ignore_preservation import (
        preserve_ignored_links,
    )

    broken_url = "https://this-link-is-not-working.de"
    content_type = ContentType.objects.get_for_model(PageTranslation)

    # Page A (augsburg/de) contains the URL and gets it marked as verified
    page_a = Page.objects.filter(region__slug="augsburg").first()
    translation_a = (
        PageTranslation.objects.filter(page=page_a, language__slug="de")
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=translation_a.pk).update(
        content=f'<a href="{broken_url}">verified link</a>',
    )
    translation_a.refresh_from_db()
    do_check_instance_links(PageTranslation, translation_a, PageTranslation._linklist)
    Link.objects.filter(
        content_type=content_type,
        object_id=translation_a.pk,
        url__url=broken_url,
    ).update(ignore=True)

    # A *different* page B in the same region gains the same URL
    page_b = Page.objects.filter(region__slug="augsburg").exclude(pk=page_a.pk).first()
    translation_b = (
        PageTranslation.objects.filter(page=page_b, language__slug="de")
        .order_by("-version")
        .first()
    )
    new_b = translation_b.create_new_version_copy(user=None)
    new_b.content = f'<a href="{broken_url}">same link on another page</a>'
    with preserve_ignored_links(translation_b):
        translation_b.links.all().delete()
        new_b.save()
        do_check_instance_links(PageTranslation, new_b, PageTranslation._linklist)

    new_link = Link.objects.get(
        content_type=content_type,
        object_id=new_b.pk,
        url__url=broken_url,
    )
    assert new_link.ignore is True, (
        "a new content object with an already-verified URL should inherit ignore=True"
    )


@pytest.mark.django_db
def test_ignore_not_inherited_across_regions(load_test_data: None) -> None:
    """
    The verified (``ignore=True``) flag is region-scoped: a URL verified
    in one region must *not* silently suppress the same URL when it appears
    in a different region whose editors never vetted it.
    """
    from django.contrib.contenttypes.models import ContentType
    from linkcheck.models import Link
    from linkcheck.worker_tasks import do_check_instance_links

    from integreat_cms.cms.models import PageTranslation

    broken_url = "https://this-link-is-not-working.de"
    content_type = ContentType.objects.get_for_model(PageTranslation)

    # Verify the URL in augsburg
    augsburg_translation = (
        PageTranslation.objects.filter(
            page__region__slug="augsburg", language__slug="de"
        )
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=augsburg_translation.pk).update(
        content=f'<a href="{broken_url}">verified in augsburg</a>',
    )
    augsburg_translation.refresh_from_db()
    do_check_instance_links(
        PageTranslation, augsburg_translation, PageTranslation._linklist
    )
    Link.objects.filter(
        content_type=content_type,
        object_id=augsburg_translation.pk,
        url__url=broken_url,
    ).update(ignore=True)

    # The same URL appears in a page of a different region
    nurnberg_translation = (
        PageTranslation.objects.filter(
            page__region__slug="nurnberg", language__slug="de"
        )
        .order_by("-version")
        .first()
    )
    PageTranslation.objects.filter(pk=nurnberg_translation.pk).update(
        content=f'<a href="{broken_url}">not vetted in nurnberg</a>',
    )
    nurnberg_translation.refresh_from_db()
    do_check_instance_links(
        PageTranslation, nurnberg_translation, PageTranslation._linklist
    )

    nurnberg_link = Link.objects.get(
        content_type=content_type,
        object_id=nurnberg_translation.pk,
        url__url=broken_url,
    )
    assert nurnberg_link.ignore is False, "ignore=True must not leak across regions"
