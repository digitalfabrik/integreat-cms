"""
Test repair tree util

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

import pytest

from integreat_cms.cms.models import Page, Region
from integreat_cms.cms.utils.repair_tree import repair_tree

after_tests = (
    "tests/core/management/commands/test_replace_links.py::test_replace_links_commit",
    "tests/core/management/commands/test_fix_internal_links.py::test_fix_internal_links_commit",
)


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_repair_tree(load_test_data_transactional: None) -> None:
    region = Region.objects.get(slug="augsburg")

    root_page = Page(region=region, lft=2, rgt=6, tree_id=999, depth=0)
    child1_page = Page(
        region=region, lft=1, rgt=4, tree_id=999, depth=1, parent=root_page
    )
    child2_page = Page(
        region=region, lft=4, rgt=5, tree_id=999, depth=1, parent=root_page
    )

    root_page.save()
    child1_page.save()
    child2_page.save()

    # Reload from database and ensure that there is no new fix method hooked into .save()
    # that could make this test give a false positive
    root_page = Page.objects.get(pk=root_page.pk)
    child1_page = Page.objects.get(pk=child1_page.pk)
    child2_page = Page.objects.get(pk=child2_page.pk)

    assert root_page.lft == 2  # intentional mistake, should be 1
    assert root_page.rgt == 6
    assert child1_page.lft == 1  # intentional mistake, should be 2
    assert child1_page.rgt == 4  # intentional mistake, should be 3
    assert child2_page.lft == 4
    assert child2_page.rgt == 5

    repair_tree(page_id=root_page.pk, commit=True)

    # We have to reload the objects from the database
    root_page = Page.objects.get(pk=root_page.pk)
    child1_page = Page.objects.get(pk=child1_page.pk)
    child2_page = Page.objects.get(pk=child2_page.pk)

    # Actual asserts ensuring the fix was successful
    assert root_page.lft == 1
    assert root_page.rgt == 6
    assert child1_page.lft == 2
    assert child1_page.rgt == 3
    assert child2_page.lft == 4
    assert child2_page.rgt == 5

    child2_page.delete()
    child1_page.delete()
    root_page.delete()
