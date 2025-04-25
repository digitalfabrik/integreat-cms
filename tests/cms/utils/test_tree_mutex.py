"""
Test tree mutex for page tree

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

from __future__ import annotations

from threading import Thread
from typing import TYPE_CHECKING

import pytest
from django.db.utils import IntegrityError
from treebeard.exceptions import InvalidMoveToDescendant

from integreat_cms.cms.models import Page
from integreat_cms.cms.utils.tree_mutex import tree_mutex

from ...conftest import test_data_db_snapshot

if TYPE_CHECKING:
    from collections.abc import Callable

after_tests = (
    "tests/core/management/commands/test_replace_links.py::test_replace_links_commit",
    "tests/core/management/commands/test_fix_internal_links.py::test_fix_internal_links_commit",
    "tests/cms/utils/test_repair_tree.py::test_repair_tree",
)


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True)
#@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_tree_mutex(test_data_db_snapshot: None, db_snapshot: None) -> None:
    """
    Check whether :func:`~integreat_cms.cms.utils.tree_mutex.tree_mutex` is actually preventing collisions.
    See :func:`run_mutex_test` for details.
    """
    run_mutex_test(use_mutex=True)


@pytest.mark.order("last", after=(*after_tests, "test_tree_mutex"))
@pytest.mark.django_db(transaction=True)
#@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_rule_out_false_positive(test_data_db_snapshot: None, db_snapshot: None) -> None:
    """
    Rule out that :func:`~integreat_cms.cms.utils.tree_mutex.tree_mutex` is just doing nothing and :func:`test_tree_mutex`
    only succeeded because the system magically worked without it.
    Provoke and expect a variety of possible exceptions using :func:`run_mutex_test`.

    If this test fails with an exception not expected and you can prove that it is indicative of
    treebeard shooting itself in the foot, please add the exception as expected!
    """
    with pytest.raises(
        (
            IntegrityError,
            AttributeError,
            IndexError,
            Page.DoesNotExist,
            InvalidMoveToDescendant,
        )
    ) as exc_info:
        run_mutex_test(use_mutex=False)

    if isinstance(exc_info.value, AttributeError):
        assert (
            exc_info.value.args[0]
            == "'NoneType' object has no attribute 'is_descendant_of'"
        )


def run_mutex_test(use_mutex: bool) -> None:
    """
    Start two :func:`five_ten_five` tests in parallel, in separate threads.
    These each constantly move their "contestant" page back and forth.
    TreeBeard seems to quickly run into inconsistencies,
    as their code bypasses Djangos Object-Relationional Mapper (ORM),
    directly running raw SQL commands, without database transactions.
    """
    exception = None

    assert Page.objects.get(id=19)
    assert Page.objects.get(id=21)

    def handle_exception(e: Exception) -> None:
        nonlocal exception
        exception = e

    one = Thread(
        target=five_ten_five,
        kwargs={
            "contestant_id": 21,
            "use_mutex": use_mutex,
            "handle_exception": handle_exception,
        },
    )
    two = Thread(
        target=five_ten_five,
        kwargs={
            "contestant_id": 19,
            "use_mutex": use_mutex,
            "handle_exception": handle_exception,
        },
    )

    print("starting threads…")
    one.start()
    two.start()

    one.join()
    two.join()
    print("joined threads!")

    if exception:
        # Raise the exception from the child thread here in the main thread
        raise exception


def five_ten_five(
    contestant_id: int,
    use_mutex: bool,
    handle_exception: Callable | None = None,
) -> None:
    """
    Move a "contestant" page back and forth repeatedly.
    Exceptions are caught and handed to ``handle_exception``,
    this is necessary to get them back out to the main thread.
    ``use_mutex`` dictates whether to use :func:`mforth`/:func:`mback`
    or :func:`forth`/:func:`back`.
    """
    print(
        f"running 5-10-5 on contestant #{contestant_id} {'with' if use_mutex else 'without'} tree_mutex"
    )
    try:
        for i in range(5):
            print(f"    [#{contestant_id}] {i}")
            if use_mutex:
                mforth(contestant_id)
                mback(contestant_id)
            else:
                forth(contestant_id)
                back(contestant_id)
    except Exception as e:  # noqa: BLE001
        if handle_exception:
            handle_exception(e)
        print(
            f"failed 5-10-5 of contestant #{contestant_id} {'with' if use_mutex else 'without'} tree_mutex:\n  {e!r}"
        )
    else:
        print(
            f"finished 5-10-5 of contestant #{contestant_id} {'with' if use_mutex else 'without'} tree_mutex"
        )


@tree_mutex("page")
def mforth(contestant_id: int) -> None:
    """
    Only calls :func:`forth`, but decorated with :func:`~integreat_cms.cms.utils.tree_mutex.tree_mutex`.
    """
    forth(contestant_id)


@tree_mutex("page")
def mback(contestant_id: int) -> None:
    """
    Only calls :func:`back`, but decorated with :func:`~integreat_cms.cms.utils.tree_mutex.tree_mutex`.
    """
    back(contestant_id)


def forth(contestant_id: int) -> None:
    """
    Gets the page with id ``contestant_id`` and the target page with id ``20``
    and moves the contestant in as the last child of the target.
    """
    print(f"   moving contestant #{contestant_id}…")
    contestant = Page.objects.get(id=contestant_id)
    assert contestant is not None
    other = Page.objects.get(id=20)
    assert other is not None
    contestant.move(other, "last-child")
    print(f"OK moving contestant #{contestant_id}!")


def back(contestant_id: int) -> None:
    """
    Gets the page with id ``contestant_id`` and the target page with id ``20``
    and moves the contestant out as the right sibling of the target.
    """
    print(f"   moving back contestant #{contestant_id}…")
    contestant = Page.objects.get(id=contestant_id)
    assert contestant is not None
    other = Page.objects.get(id=20)
    assert other is not None
    contestant.move(other, "right")
    print(f"OK moving back contestant #{contestant_id}!")
