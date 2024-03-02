"""
This module contains a custom decorator for db / redis mutexes
"""

import time
from typing import Any, Callable, ParamSpec, Type, TypeVar
from uuid import uuid4

from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, transaction
from treebeard.models import Node

LOCK_SECONDS = 10
INTERVAL = 0.1


def build_monkeypatched_cursor_func(
    using: str = DEFAULT_DB_ALIAS,
) -> "classmethod[Any, [str], None]":
    """
    patch upstream transaction to expose the database cursor
    """
    connection = transaction.get_connection(using=using)

    def get_monkeypatch_cursor(cls: Type, action: str) -> None:
        print(f"someone is getting our monkeypatched cursor ({using})! {cls}, {action}")
        return connection.cursor()

    return classmethod(get_monkeypatch_cursor)


# pylint: disable=protected-access
get_old_cursor_func = Node._get_database_cursor

R = TypeVar("R")
P = ParamSpec("P")


def tree_mutex(classname: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Collect decorator argument
    """

    def wrap(func: Callable[P, R]) -> Callable[P, R]:
        """
        define decorator that acts as a mutex
        """

        # pylint: disable=protected-access
        def innermost_function(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            mutex logic
            """
            lock_name = f"MUTEX_{classname}_TREE"
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
