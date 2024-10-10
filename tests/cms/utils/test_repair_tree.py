"""
Test repair tree util

Test execution order:
Since there seem to be some weird side effects happening
for unrelated tests when testing database consistency, we first run those,
then the tests that make sure the :func:`~integreat_cms.cms.utils.repair_tree.repair_tree` is effective,
and last the effectiveness of :func:`~integreat_cms.cms.utils.tree_mutex.tree_mutex` itself.
This ordering is facilitated using pytest_order
to specify the tests to run ``"last"`` (eqivalent to ``-1``, absolute ordering)
and after certain other tests (relative ordering).

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
    """
    Create a broken tree of 3 nodes and assert that :func:`~integreat_cms.cms.utils.repair_tree.repair_tree` correctly fixes it.
    """
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

    repair_tree(page_id=[root_page.pk], commit=True)

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

    assert root_page.depth == 1
    assert child1_page.depth == 2
    assert child2_page.depth == 2

    child2_page.delete()
    child1_page.delete()
    root_page.delete()


@pytest.mark.xfail(
    reason="Constraints on the model prohibit the broken state used as basis for this test"
)
@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_repair_tree_complex(  # pylint: disable=too-many-locals, too-many-statements # noqa: PLR0915
    load_test_data_transactional: None,
) -> None:
    """
    Recreate a real-world example of a broken tree and assert that :func:`~integreat_cms.cms.utils.repair_tree.repair_tree` correctly fixes it.
    """
    region = Region.objects.get(slug="augsburg")

    A = Page(region=region, lft=1, rgt=58, tree_id=19730, depth=1)
    A_1 = Page(region=region, lft=2, rgt=3, tree_id=19730, depth=2, parent=A)
    A_2 = Page(region=region, lft=4, rgt=13, tree_id=19730, depth=2, parent=A)
    A_2_1 = Page(region=region, lft=4, rgt=13, tree_id=19730, depth=2, parent=A_2)
    A_2_2 = Page(region=region, lft=7, rgt=8, tree_id=19730, depth=3, parent=A_2)
    A_2_3 = Page(region=region, lft=9, rgt=10, tree_id=19730, depth=3, parent=A_2)
    A_2_4 = Page(region=region, lft=11, rgt=12, tree_id=19730, depth=3, parent=A_2)
    A_3 = Page(region=region, lft=14, rgt=15, tree_id=19730, depth=2, parent=A)
    A_4 = Page(region=region, lft=16, rgt=17, tree_id=19730, depth=2, parent=A)
    A_5 = Page(region=region, lft=18, rgt=29, tree_id=19730, depth=2, parent=A)
    A_5_1 = Page(region=region, lft=19, rgt=20, tree_id=19730, depth=3, parent=A_5)
    A_5_2 = Page(region=region, lft=21, rgt=22, tree_id=19730, depth=3, parent=A_5)
    A_5_3 = Page(region=region, lft=23, rgt=24, tree_id=19730, depth=3, parent=A_5)
    A_5_4 = Page(region=region, lft=25, rgt=26, tree_id=19730, depth=3, parent=A_5)
    A_5_5 = Page(region=region, lft=27, rgt=28, tree_id=19730, depth=3, parent=A_5)
    A_6 = Page(region=region, lft=30, rgt=31, tree_id=19730, depth=2, parent=A)
    A_7 = Page(region=region, lft=32, rgt=33, tree_id=19730, depth=2, parent=A)
    A_8 = Page(region=region, lft=34, rgt=39, tree_id=19730, depth=2, parent=A)
    A_8_1 = Page(region=region, lft=35, rgt=36, tree_id=19730, depth=3, parent=A_8)
    A_8_2 = Page(region=region, lft=37, rgt=38, tree_id=19730, depth=3, parent=A_8)
    A_9 = Page(region=region, lft=40, rgt=41, tree_id=19730, depth=2, parent=A)
    A_10 = Page(region=region, lft=42, rgt=43, tree_id=19730, depth=2, parent=A)
    A_11 = Page(region=region, lft=44, rgt=45, tree_id=19730, depth=2, parent=A)
    A_12 = Page(region=region, lft=46, rgt=51, tree_id=19730, depth=2, parent=A)
    A_12_1 = Page(region=region, lft=47, rgt=48, tree_id=19730, depth=3, parent=A_12)
    A_12_2 = Page(region=region, lft=49, rgt=50, tree_id=19730, depth=3, parent=A_12)
    A_13 = Page(region=region, lft=52, rgt=57, tree_id=19730, depth=2, parent=A)
    A_13_1 = Page(region=region, lft=53, rgt=54, tree_id=19730, depth=3, parent=A_13)
    A_13_2 = Page(region=region, lft=55, rgt=56, tree_id=19730, depth=3, parent=A_13)

    B = Page(region=region, lft=1, rgt=32, tree_id=19732, depth=1, parent=None)
    B_1 = Page(region=region, lft=2, rgt=13, tree_id=19732, depth=2, parent=B)
    B_1_1 = Page(region=region, lft=3, rgt=6, tree_id=19732, depth=3, parent=B_1)
    B_1_2 = Page(region=region, lft=7, rgt=10, tree_id=19732, depth=3, parent=B_1)
    B_1_3 = Page(region=region, lft=11, rgt=12, tree_id=19732, depth=3, parent=B_1)
    B_2 = Page(region=region, lft=14, rgt=15, tree_id=19732, depth=2, parent=B)
    B_3 = Page(region=region, lft=16, rgt=17, tree_id=19732, depth=2, parent=B)
    B_4 = Page(region=region, lft=18, rgt=25, tree_id=19732, depth=2, parent=B)
    B_4_1 = Page(region=region, lft=19, rgt=20, tree_id=19732, depth=3, parent=B_4)
    B_4_2 = Page(region=region, lft=21, rgt=22, tree_id=19732, depth=3, parent=B_4)
    B_4_3 = Page(region=region, lft=23, rgt=24, tree_id=19732, depth=3, parent=B_4)
    B_5 = Page(region=region, lft=26, rgt=27, tree_id=19732, depth=2, parent=B)
    B_6 = Page(region=region, lft=28, rgt=29, tree_id=19732, depth=2, parent=B)
    B_7 = Page(region=region, lft=30, rgt=31, tree_id=19732, depth=2, parent=B)

    orphan1 = Page(region=region, lft=4, rgt=5, tree_id=19730, depth=3, parent=B_1_1)
    orphan2 = Page(region=region, lft=8, rgt=9, tree_id=19730, depth=3, parent=B_1_2)

    A.save()
    A_1.save()
    A_2.save()
    A_2_1.save()
    A_2_2.save()
    A_2_3.save()
    A_2_4.save()
    A_3.save()
    A_4.save()
    A_5.save()
    A_5_1.save()
    A_5_2.save()
    A_5_3.save()
    A_5_4.save()
    A_5_5.save()
    A_6.save()
    A_7.save()
    A_8.save()
    A_8_1.save()
    A_8_2.save()
    A_9.save()
    A_10.save()
    A_11.save()
    A_12.save()
    A_12_1.save()
    A_12_2.save()
    A_13.save()
    A_13_1.save()
    A_13_2.save()

    B.save()
    B_1.save()
    B_1_1.save()
    B_1_2.save()
    B_1_3.save()
    B_2.save()
    B_3.save()
    B_4.save()
    B_4_1.save()
    B_4_2.save()
    B_4_3.save()
    B_5.save()
    B_6.save()
    B_7.save()

    orphan1.save()
    orphan2.save()

    # Reload from database and ensure that there is no new fix method hooked into .save()
    # that could make this test give a false positive
    A = Page.objects.get(pk=A.pk)
    A_1 = Page.objects.get(pk=A_1.pk)
    A_2 = Page.objects.get(pk=A_2.pk)
    A_2_1 = Page.objects.get(pk=A_2_1.pk)
    A_2_2 = Page.objects.get(pk=A_2_2.pk)
    A_2_3 = Page.objects.get(pk=A_2_3.pk)
    A_2_4 = Page.objects.get(pk=A_2_4.pk)
    A_3 = Page.objects.get(pk=A_3.pk)
    A_4 = Page.objects.get(pk=A_4.pk)
    A_5 = Page.objects.get(pk=A_5.pk)
    A_5_1 = Page.objects.get(pk=A_5_1.pk)
    A_5_2 = Page.objects.get(pk=A_5_2.pk)
    A_5_3 = Page.objects.get(pk=A_5_3.pk)
    A_5_4 = Page.objects.get(pk=A_5_4.pk)
    A_5_5 = Page.objects.get(pk=A_5_5.pk)
    A_6 = Page.objects.get(pk=A_6.pk)
    A_7 = Page.objects.get(pk=A_7.pk)
    A_8 = Page.objects.get(pk=A_8.pk)
    A_8_1 = Page.objects.get(pk=A_8_1.pk)
    A_8_2 = Page.objects.get(pk=A_8_2.pk)
    A_9 = Page.objects.get(pk=A_9.pk)
    A_10 = Page.objects.get(pk=A_10.pk)
    A_11 = Page.objects.get(pk=A_11.pk)
    A_12 = Page.objects.get(pk=A_12.pk)
    A_12_1 = Page.objects.get(pk=A_12_1.pk)
    A_12_2 = Page.objects.get(pk=A_12_2.pk)
    A_13 = Page.objects.get(pk=A_13.pk)
    A_13_1 = Page.objects.get(pk=A_13_1.pk)
    A_13_2 = Page.objects.get(pk=A_13_2.pk)

    B = Page.objects.get(pk=B.pk)
    B_1 = Page.objects.get(pk=B_1.pk)
    B_1_1 = Page.objects.get(pk=B_1_1.pk)
    B_1_2 = Page.objects.get(pk=B_1_2.pk)
    B_1_3 = Page.objects.get(pk=B_1_3.pk)
    B_2 = Page.objects.get(pk=B_2.pk)
    B_3 = Page.objects.get(pk=B_3.pk)
    B_4 = Page.objects.get(pk=B_4.pk)
    B_4_1 = Page.objects.get(pk=B_4_1.pk)
    B_4_2 = Page.objects.get(pk=B_4_2.pk)
    B_4_3 = Page.objects.get(pk=B_4_3.pk)
    B_5 = Page.objects.get(pk=B_5.pk)
    B_6 = Page.objects.get(pk=B_6.pk)
    B_7 = Page.objects.get(pk=B_7.pk)

    orphan1 = Page.objects.get(pk=orphan1.pk)
    orphan2 = Page.objects.get(pk=orphan2.pk)

    assert orphan1.parent == B_1_1
    assert orphan1.parent_id == B_1_1.pk
    assert orphan2.parent == B_1_2
    assert orphan2.parent_id == B_1_2.pk

    assert A.lft == 1
    assert A.rgt == 58
    assert A.tree_id == 19730
    assert A.depth == 1
    assert A_1.lft == 2
    assert A_1.rgt == 3
    assert A_2.lft == 4
    assert A_2.rgt == 13
    assert A_2_1.lft == 4
    assert A_2_1.rgt == 13
    assert A_2_2.lft == 7
    assert A_2_2.rgt == 8
    assert A_2_3.lft == 9
    assert A_2_3.rgt == 10
    assert A_2_4.lft == 11
    assert A_2_4.rgt == 12
    assert A_3.lft == 14
    assert A_3.rgt == 15
    assert A_4.lft == 16
    assert A_4.rgt == 17
    assert A_5.lft == 18
    assert A_5.rgt == 29
    assert A_5_1.lft == 19
    assert A_5_1.rgt == 20
    assert A_5_2.lft == 21
    assert A_5_2.rgt == 22
    assert A_5_3.lft == 23
    assert A_5_3.rgt == 24
    assert A_5_4.lft == 25
    assert A_5_4.rgt == 26
    assert A_5_5.lft == 27
    assert A_5_5.rgt == 28
    assert A_6.lft == 30
    assert A_6.rgt == 31
    assert A_7.lft == 32
    assert A_7.rgt == 33
    assert A_8.lft == 34
    assert A_8.rgt == 39
    assert A_8_1.lft == 35
    assert A_8_1.rgt == 36
    assert A_8_2.lft == 37
    assert A_8_2.rgt == 38
    assert A_9.lft == 40
    assert A_9.rgt == 41
    assert A_10.lft == 42
    assert A_10.rgt == 43
    assert A_11.lft == 44
    assert A_11.rgt == 45
    assert A_12.lft == 46
    assert A_12.rgt == 51
    assert A_12_1.lft == 47
    assert A_12_1.rgt == 48
    assert A_12_2.lft == 49
    assert A_12_2.rgt == 50
    assert A_13.lft == 52
    assert A_13.rgt == 57
    assert A_13_1.lft == 53
    assert A_13_1.rgt == 54
    assert A_13_2.lft == 55
    assert A_13_2.rgt == 56

    assert B.lft == 1
    assert B.rgt == 32
    assert B.tree_id == 19732
    assert B.depth == 1
    assert B_1.lft == 2
    assert B_1.rgt == 13
    assert B_1_1.lft == 3
    assert B_1_1.rgt == 6
    assert B_1_2.lft == 7
    assert B_1_2.rgt == 10
    assert B_1_3.lft == 11
    assert B_1_3.rgt == 12
    assert B_2.lft == 14
    assert B_2.rgt == 15
    assert B_3.lft == 16
    assert B_3.rgt == 17
    assert B_4.lft == 18
    assert B_4.rgt == 25
    assert B_4_1.lft == 19
    assert B_4_1.rgt == 20
    assert B_4_2.lft == 21
    assert B_4_2.rgt == 22
    assert B_4_3.lft == 23
    assert B_4_3.rgt == 24
    assert B_5.lft == 26
    assert B_5.rgt == 27
    assert B_6.lft == 28
    assert B_6.rgt == 29
    assert B_7.lft == 30
    assert B_7.rgt == 31

    assert orphan1.lft == 4
    assert orphan1.rgt == 5
    assert orphan1.tree_id == 19730
    assert orphan1.depth == 3
    assert orphan2.lft == 8
    assert orphan2.rgt == 9
    assert orphan2.tree_id == 19730
    assert orphan2.depth == 3

    repair_tree(page_id=[A_1.pk, B_1.pk], commit=True)

    # We have to reload the objects from the database
    A = Page.objects.get(pk=A.pk)
    A_1 = Page.objects.get(pk=A_1.pk)
    A_2 = Page.objects.get(pk=A_2.pk)
    A_2_1 = Page.objects.get(pk=A_2_1.pk)
    A_2_2 = Page.objects.get(pk=A_2_2.pk)
    A_2_3 = Page.objects.get(pk=A_2_3.pk)
    A_2_4 = Page.objects.get(pk=A_2_4.pk)
    A_3 = Page.objects.get(pk=A_3.pk)
    A_4 = Page.objects.get(pk=A_4.pk)
    A_5 = Page.objects.get(pk=A_5.pk)
    A_5_1 = Page.objects.get(pk=A_5_1.pk)
    A_5_2 = Page.objects.get(pk=A_5_2.pk)
    A_5_3 = Page.objects.get(pk=A_5_3.pk)
    A_5_4 = Page.objects.get(pk=A_5_4.pk)
    A_5_5 = Page.objects.get(pk=A_5_5.pk)
    A_6 = Page.objects.get(pk=A_6.pk)
    A_7 = Page.objects.get(pk=A_7.pk)
    A_8 = Page.objects.get(pk=A_8.pk)
    A_8_1 = Page.objects.get(pk=A_8_1.pk)
    A_8_2 = Page.objects.get(pk=A_8_2.pk)
    A_9 = Page.objects.get(pk=A_9.pk)
    A_10 = Page.objects.get(pk=A_10.pk)
    A_11 = Page.objects.get(pk=A_11.pk)
    A_12 = Page.objects.get(pk=A_12.pk)
    A_12_1 = Page.objects.get(pk=A_12_1.pk)
    A_12_2 = Page.objects.get(pk=A_12_2.pk)
    A_13 = Page.objects.get(pk=A_13.pk)
    A_13_1 = Page.objects.get(pk=A_13_1.pk)
    A_13_2 = Page.objects.get(pk=A_13_2.pk)

    B = Page.objects.get(pk=B.pk)
    B_1 = Page.objects.get(pk=B_1.pk)
    B_1_1 = Page.objects.get(pk=B_1_1.pk)
    B_1_2 = Page.objects.get(pk=B_1_2.pk)
    B_1_3 = Page.objects.get(pk=B_1_3.pk)
    B_2 = Page.objects.get(pk=B_2.pk)
    B_3 = Page.objects.get(pk=B_3.pk)
    B_4 = Page.objects.get(pk=B_4.pk)
    B_4_1 = Page.objects.get(pk=B_4_1.pk)
    B_4_2 = Page.objects.get(pk=B_4_2.pk)
    B_4_3 = Page.objects.get(pk=B_4_3.pk)
    B_5 = Page.objects.get(pk=B_5.pk)
    B_6 = Page.objects.get(pk=B_6.pk)
    B_7 = Page.objects.get(pk=B_7.pk)

    orphan1 = Page.objects.get(pk=orphan1.pk)
    orphan2 = Page.objects.get(pk=orphan2.pk)

    # Actual asserts ensuring the fix was successful
    assert A.tree_id != B.tree_id
    assert orphan1.tree_id == B.tree_id
    assert orphan2.tree_id == B.tree_id

    assert A.lft == 1
    assert A_1.lft == 2
    assert A_1.rgt == 3
    assert A_2.lft == 4
    assert A_2_1.lft == 5
    assert A_2_1.rgt == 6
    assert A_2_2.lft == 7
    assert A_2_2.rgt == 8
    assert A_2_3.lft == 9
    assert A_2_3.rgt == 10
    assert A_2_4.lft == 11
    assert A_2_4.rgt == 12
    assert A_2.rgt == 13
    assert A_3.lft == 14
    assert A_3.rgt == 15
    assert A_4.lft == 16
    assert A_4.rgt == 17
    assert A_5.lft == 18
    assert A_5_1.lft == 19
    assert A_5_1.rgt == 20
    assert A_5_2.lft == 21
    assert A_5_2.rgt == 22
    assert A_5_3.lft == 23
    assert A_5_3.rgt == 24
    assert A_5_4.lft == 25
    assert A_5_4.rgt == 26
    assert A_5_5.lft == 27
    assert A_5_5.rgt == 28
    assert A_5.rgt == 29
    assert A_6.lft == 30
    assert A_6.rgt == 31
    assert A_7.lft == 32
    assert A_7.rgt == 33
    assert A_8.lft == 34
    assert A_8_1.lft == 35
    assert A_8_1.rgt == 36
    assert A_8_2.lft == 37
    assert A_8_2.rgt == 38
    assert A_8.rgt == 39
    assert A_9.lft == 40
    assert A_9.rgt == 41
    assert A_10.lft == 42
    assert A_10.rgt == 43
    assert A_11.lft == 44
    assert A_11.rgt == 45
    assert A_12.lft == 46
    assert A_12_1.lft == 47
    assert A_12_1.rgt == 48
    assert A_12_2.lft == 49
    assert A_12_2.rgt == 50
    assert A_12.rgt == 51
    assert A_13.lft == 52
    assert A_13_1.lft == 53
    assert A_13_1.rgt == 54
    assert A_13_2.lft == 55
    assert A_13_2.rgt == 56
    assert A_13.rgt == 57
    assert A.rgt == 58

    assert B.lft == 1
    assert B_1.lft == 2
    assert B_1_1.lft == 3
    assert orphan1.lft == 4
    assert orphan1.rgt == 5
    assert B_1_1.rgt == 6
    assert B_1_2.lft == 7
    assert orphan2.lft == 8
    assert orphan2.rgt == 9
    assert B_1_2.rgt == 10
    assert B_1_3.lft == 11
    assert B_1_3.rgt == 12
    assert B_1.rgt == 13
    assert B_2.lft == 14
    assert B_2.rgt == 15
    assert B_3.lft == 16
    assert B_3.rgt == 17
    assert B_4.lft == 18
    assert B_4_1.lft == 19
    assert B_4_1.rgt == 20
    assert B_4_2.lft == 21
    assert B_4_2.rgt == 22
    assert B_4_3.lft == 23
    assert B_4_3.rgt == 24
    assert B_4.rgt == 25
    assert B_5.lft == 26
    assert B_5.rgt == 27
    assert B_6.lft == 28
    assert B_6.rgt == 29
    assert B_7.lft == 30
    assert B_7.rgt == 31
    assert B.rgt == 32

    assert orphan1.depth == 4
    assert orphan2.depth == 4

    # Delete in reverse to avoid protected foreign keys
    orphan2.delete()
    orphan1.delete()

    B_7.delete()
    B_6.delete()
    B_5.delete()
    B_4_3.delete()
    B_4_2.delete()
    B_4_1.delete()
    B_4.delete()
    B_3.delete()
    B_2.delete()
    B_1_3.delete()
    B_1_2.delete()
    B_1_1.delete()
    B_1.delete()
    B.delete()

    A_13_2.delete()
    A_13_1.delete()
    A_13.delete()
    A_12_2.delete()
    A_12_1.delete()
    A_12.delete()
    A_11.delete()
    A_10.delete()
    A_9.delete()
    A_8_2.delete()
    A_8_1.delete()
    A_8.delete()
    A_7.delete()
    A_6.delete()
    A_5_5.delete()
    A_5_4.delete()
    A_5_3.delete()
    A_5_2.delete()
    A_5_1.delete()
    A_5.delete()
    A_4.delete()
    A_3.delete()
    A_2_4.delete()
    A_2_3.delete()
    A_2_2.delete()
    A_2_1.delete()
    A_2.delete()
    A_1.delete()
    A.delete()
