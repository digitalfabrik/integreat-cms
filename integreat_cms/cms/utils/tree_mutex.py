"""
This module contains a custom decorator for db / redis mutexes
"""

import functools
import time
from typing import Any, Callable, ParamSpec, Type, TypeVar
from uuid import uuid4

from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, transaction
from treebeard.models import Node

#: For how many seconds the lock persists, and the timeout for retrying to acquire it.
LOCK_SECONDS = 10
#: How long to sleep between retries to acquire the lock.
INTERVAL = 0.1


def build_monkeypatched_cursor_func(
    using: str = DEFAULT_DB_ALIAS,
) -> "classmethod[Any, [str], None]":
    """
    Ger connection for upstream transaction and
    build alternative :meth:`treebeard.models.Node._get_database_cursor` that returns its cursor instead.
    """
    connection = transaction.get_connection(using=using)

    def get_monkeypatch_cursor(cls: Type, action: str) -> None:
        """
        A fake classmethod to overwrite :meth:`treebeard.models.Node._get_database_cursor` with.
        Gets the cursor for the currend django connection instead,
        allowing treebeard to be forced to use database transactions.
        """
        print(f"someone is getting our monkeypatched cursor ({using})! {cls}, {action}")
        return connection.cursor()

    return classmethod(get_monkeypatch_cursor)


# pylint: disable=protected-access
get_old_cursor_func = Node._get_database_cursor

R = TypeVar("R")
P = ParamSpec("P")


def tree_mutex(classname: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to prevent treebeard from screwing up the database.
    In addition to implementing a mutex,
    we use :func:`django.db.transaction.atomic`
    and monkey patch :meth:`treebeard.models.Node._get_database_cursor`
    to actually use djangos database cursor and force it into db transactions that way.

    The lock is implemented using a :func:`~uuid.uuid4` with :func:`django.core.cache.backends.base.BaseCache.get_or_set`,
    while separate locks are maintained per class.
    This allows page trees to be locked separately from POIs etc.,
    but requires strict conformance to always specify the exact ``classname`` when using the decorator.
    If there is a typo, there will be no indication at server startup, and collisions and data corruption may occur.

    If the lock cannot be acquired, this sleeps for ``INTERVAL`` seconds.
    After ``LOCK_SECONDS`` without acquiring the lock it fails, raising a :class:`TimeoutError`.
    """

    def wrap(func: Callable[P, R]) -> Callable[P, R]:
        """
        This is the actual decorator that takes ``func`` and returns a function with the same signature.
        The outer function :func:`tree_mutex` is necessary to get the ``classname`` variable.
        """

        # pylint: disable=protected-access
        @functools.wraps(func)
        def innermost_function(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The function replacing the decorated function.
            Acquire the lock, invoke :func:`django.db.transaction.atomic`,
            monkey patch :meth:`treebeard.models.Node._get_database_cursor` to get djangos db cursor
            and finally call the decorated ``func``.

            :raises TimeoutError: When the lock wasn't available after ``LOCK_SECONDS`` s, trying every ``INTERVAL`` s.
            """
            lock_name = f"MUTEX_{classname.upper()}_TREE"
            uuid = uuid4()
            timeout = time.time() + LOCK_SECONDS
            while time.time() < timeout:
                if (
                    active_lock := cache.get_or_set(lock_name, uuid, LOCK_SECONDS)
                ) == uuid:
                    try:
                        with transaction.atomic(using=DEFAULT_DB_ALIAS, durable=True):
                            old_cursor_func = Node._get_database_cursor
                            Node._get_database_cursor = build_monkeypatched_cursor_func(
                                DEFAULT_DB_ALIAS
                            )
                            value = func(*args, **kwargs)
                            Node._get_database_cursor = old_cursor_func
                            return value
                    finally:
                        print(
                            f"  Releasing {lock_name} after {time.time() - (timeout - LOCK_SECONDS)}s ({uuid})"
                        )
                        cache.delete(lock_name)
                else:
                    print(
                        f"  Failed to acquire {lock_name} as {uuid}: MUTEX_{classname}_TREE present ({active_lock}). Waiting {INTERVAL}s…"
                    )
                    time.sleep(INTERVAL)
            raise TimeoutError(f"Failed to acquire {classname} lock")

        return innermost_function

    return wrap
