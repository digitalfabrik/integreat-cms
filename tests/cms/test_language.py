from __future__ import annotations

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Language, LanguageTreeNode, Region
from tests.conftest import ANONYMOUS, HIGH_PRIV_STAFF_ROLES


@pytest.mark.django_db
def test_create_new_language_node(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    region = Region.objects.filter(slug="nurnberg").first()
    # Ukrainian will be used for the test because the region Nürnberg does not have it.
    new_language = Language.objects.filter(slug="uk").first()
    parent = region.language_tree_root

    # Check the new language does not exist in the region
    assert not new_language in region.languages

    next_url = url = reverse(
        "new_languagetreenode", kwargs={"region_slug": region.slug}
    )
    response = client.post(
        url,
        data={
            "language": new_language.id,
            "visible": True,
            "active": True,
            "parent": parent.id,
            "machine_translation_enabled": True,
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        # Verify the new language node was created
        assert (
            LanguageTreeNode.objects.filter(
                region=region, language=new_language
            ).count()
            == 1
        )
        # Verify now both Augsburg and Nürnberg have a language node with Ukrainian
        assert LanguageTreeNode.objects.filter(language=new_language).count() == 2
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_update_language_node(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Change the parent of Farsi node from Arabic to German
    region = Region.objects.filter(slug="nurnberg").first()
    language = Language.objects.filter(slug="fa").first()
    language_node = LanguageTreeNode.objects.filter(
        region=region, language=language
    ).first()
    root_language_node = region.language_tree_root

    # Make sure the parent node is not German
    assert not language_node.parent.id == root_language_node.id

    next_url = url = reverse(
        "edit_languagetreenode",
        kwargs={"region_slug": region.slug, "pk": language_node.id},
    )
    response = client.post(
        url,
        data={
            "language": language,
            "visible": True,
            "active": True,
            "parent": root_language_node.id,
            "machine_translation_enabled": True,
        },
    )

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        # Verify that the parent node is now German
        assert (
            LanguageTreeNode.objects.filter(region=region, language=language)
            .first()
            .parent.id
            == root_language_node.id
        )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_move_language_node(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    # Use the region Augsburg because it has many language nodes and multiple generations
    region = Region.objects.filter(slug="augsburg").first()
    language = Language.objects.filter(slug="ar").first()
    language_node = LanguageTreeNode.objects.filter(
        language=language, region=region
    ).first()

    next_url = url = reverse(
        "move_languagetreenode",
        kwargs={
            "region_slug": region.slug,
            "pk": language_node.id,
            "target_id": 9,
            "target_position": "left",
        },
    )
    response = client.post(url)

    if role in HIGH_PRIV_STAFF_ROLES:
        assert response.status_code == 302
        assert (
            LanguageTreeNode.objects.filter(language=language, region=region)
            .first()
            .parent.id
            == 1
        )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={next_url}"
        )
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_delete_language_node(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    # Log the user in
    client, role = login_role_user

    region = Region.objects.filter(slug="augsburg").first()
    # Choose a node without children to verify the delete function successes
    deletable_language = Language.objects.filter(slug="ar").first()
    deletable_language_node = LanguageTreeNode.objects.filter(
        language=deletable_language, region=region
    ).first()
    # Choose a node with children to verify the delete function is cancelled
    not_deletable_language = Language.objects.filter(slug="en").first()
    not_deletable_language_node = LanguageTreeNode.objects.filter(
        language=not_deletable_language, region=region
    ).first()

    deletable_next_url = deletable_url = reverse(
        "delete_languagetreenode",
        kwargs={"region_slug": region.slug, "pk": deletable_language_node.id},
    )
    response_success = client.post(deletable_url)
    not_deletable_next_url = not_deletable_url = reverse(
        "delete_languagetreenode",
        kwargs={"region_slug": region.slug, "pk": not_deletable_language_node.id},
    )
    response_fail = client.post(not_deletable_url)

    if role in HIGH_PRIV_STAFF_ROLES:
        # In both cases it should be redirected
        assert response_success.status_code == 302
        assert response_fail.status_code == 302
        # Verify that the language node without children was deleted
        assert not LanguageTreeNode.objects.filter(
            language=deletable_language, region=region
        ).first()
        # Verify that the language node with child nodes was not deleted
        assert LanguageTreeNode.objects.filter(
            language=not_deletable_language, region=region
        ).first()
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response_success.status_code == 302
        assert response_fail.status_code == 302
        assert (
            response_success.headers.get("location")
            == f"{settings.LOGIN_URL}?next={deletable_next_url}"
        )
        assert (
            response_fail.headers.get("location")
            == f"{settings.LOGIN_URL}?next={not_deletable_next_url}"
        )
    else:
        assert response_success.status_code == 403
        assert response_fail.status_code == 403
