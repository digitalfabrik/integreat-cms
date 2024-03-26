"""
Test repair tree management command

Test execution order:
Since there seem to be some weird side effects happening
for unrelated tests when testing database consistency, we first run those,
then these tests that make sure the repair_tree() is effective,
and last the effectiveness of @tree_mutex() itself.
This ordering is facilitated using pytest_order
to specify the tests to run "last" (eqivalent to -1, absolute ordering)
and after certain other tests (relative ordering)
See https://pytest-order.readthedocs.io/en/stable/usage.html#order-relative-to-other-tests
"""

from __future__ import annotations

import pytest

from integreat_cms.cms.models import Page, Region

from ..utils import get_command_output

after_tests = ("tests/cms/utils/test_repair_tree.py::test_repair_tree",)


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_check_clean_tree_fields(load_test_data_transactional: None) -> None:
    """
    Ensure no errors are found in default test data
    """
    assert Region.objects.all().count() > 0
    assert Page.objects.all().count() > 0

    for region in Region.objects.all():
        for root in Page.get_root_pages(region.slug):
            out, err = get_command_output("repair_tree", page_id=root.id)
            assert (
                f"Detecting problems in tree with id {root.tree_id}... ({repr(root)})"
                in out
            )
            assert not err


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_fix_clean_tree_fields(load_test_data_transactional: None) -> None:
    """
    Ensure no errors need to be fixed in default test data
    """
    assert Region.objects.all().count() > 0
    assert Page.objects.all().count() > 0

    for region in Region.objects.all():
        for root in Page.get_root_pages(region.slug):
            out, err = get_command_output("repair_tree", page_id=root.id, commit=True)
            assert f"Fixing tree with id {root.tree_id}... ({repr(root)})" in out
            assert not err


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_check_broken_tree_fields(load_test_data_transactional: None) -> None:
    """
    Ensure error is found in faulty test data
    """
    page = Page.objects.get(id=18)

    page.lft = 11
    page.rgt = 12
    page.save()

    original_tree_id = page.tree_id

    out, err = get_command_output("repair_tree", page_id=page.id)
    assert (
        f"Detecting problems in tree with id {original_tree_id}... ({repr(page)})"
        in out
    )
    assert "lft: 11 → 1" in err
    assert "rgt: 12 → 10" in err


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_fix_broken_tree_fields(load_test_data_transactional: None) -> None:
    """
    Ensure error is fixed in faulty test data
    """
    page = Page.objects.get(id=18)

    page.lft = 11
    page.rgt = 12
    page.save()

    out, err = get_command_output("repair_tree", page_id=page.id, commit=True)
    assert f"Fixing tree with id {page.tree_id}... ({repr(page)})" in out
    assert "lft: 11 → 1" in err
    assert "rgt: 12 → 10" in err

    page = Page.objects.get(id=18)
    assert page.lft == 1
    assert page.rgt == 10
