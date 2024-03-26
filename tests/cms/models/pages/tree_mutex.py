"""
Test tree mutex for page tree

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

from threading import Thread
from typing import Callable

import pytest
from django.db.utils import IntegrityError

from integreat_cms.cms.models import Page
from integreat_cms.cms.utils.tree_mutex import tree_mutex

after_tests = ("tests/cms/utils/test_repair_tree.py::test_repair_tree",)


@pytest.mark.order("last", after=after_tests)
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_tree_mutex(load_test_data_transactional: None) -> None:
    run_test(True)


@pytest.mark.order(after="test_tree_mutex")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_rule_out_false_positive(load_test_data_transactional: None) -> None:
    exception = None

    def handle_exception(e: Exception) -> None:
        nonlocal exception
        exception = e

    with pytest.raises(
        (IntegrityError, AttributeError, IndexError, Page.DoesNotExist)
    ) as exc_info:
        run_test(use_mutex=False, handle_exception=handle_exception)
        if exception:
            raise exception

    if isinstance(exc_info.value, AttributeError):
        assert (
            exc_info.value.args[0]
            == "'NoneType' object has no attribute 'is_descendant_of'"
        )


def run_test(use_mutex: bool, handle_exception: Callable | None = None) -> None:
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


def five_ten_five(
    contestant_id: int,
    use_mutex: bool,
    handle_exception: Callable | None = None,
) -> None:
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
    except Exception as e:
        if handle_exception:
            handle_exception(e)
        print(
            f"failed 5-10-5 of contestant #{contestant_id} {'with' if use_mutex else 'without'} tree_mutex:\n  {repr(e)}"
        )
    else:
        print(
            f"finished 5-10-5 of contestant #{contestant_id} {'with' if use_mutex else 'without'} tree_mutex"
        )


@tree_mutex("page")
def mforth(contestant_id: int) -> None:
    forth(contestant_id)


@tree_mutex("page")
def mback(contestant_id: int) -> None:
    back(contestant_id)


def forth(contestant_id: int) -> None:
    print(f"   moving contestant #{contestant_id}…")
    contestant = Page.objects.get(id=contestant_id)
    assert contestant is not None
    other = Page.objects.get(id=20)
    assert other is not None
    contestant.move(other, "last-child")
    print(f"OK moving contestant #{contestant_id}!")


def back(contestant_id: int) -> None:
    print(f"   moving back contestant #{contestant_id}…")
    contestant = Page.objects.get(id=contestant_id)
    assert contestant is not None
    other = Page.objects.get(id=20)
    assert other is not None
    contestant.move(other, "right")
    print(f"OK moving back contestant #{contestant_id}!")
