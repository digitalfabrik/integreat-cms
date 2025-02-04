"""
This module contains a custom decorator for db / redis mutexes
"""

import functools
import logging
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import ParamSpec, TypeVar

from django.db import DEFAULT_DB_ALIAS, transaction
from treebeard.models import Node

logger = logging.getLogger(__name__)

#: For how many seconds the lock persists, and the timeout for retrying to acquire it.
LOCK_SECONDS = 10
#: How long to sleep between retries to acquire the lock.
INTERVAL = 0.1


#: A dictionary holding separate locks for each classname to be guarded
_LOCKS = {}


@contextmanager
def monkeypatch_cursor_func(
    using: str = DEFAULT_DB_ALIAS,
) -> Generator[None, None, None]:
    """
    Get connection for upstream transaction and
    set alternative :meth:`treebeard.models.Node._get_database_cursor` that returns its cursor instead.
    Ensures that this is being called from within the same thread and context, otherwise still return original value.
    """
    connection = transaction.get_connection(using=using)
    original_get_database_cursor = Node._get_database_cursor

    def monkeypatched_get_cursor(cls: type, action: str) -> None:
        """
        A fake classmethod to overwrite :meth:`treebeard.models.Node._get_database_cursor` with.
        Gets the cursor for the currend django connection instead,
        allowing treebeard to be forced to use database transactions.
        """
        logger.debug(
            "someone is getting our monkeypatched db cursor (%s)! %r, %s",
            using,
            cls,
            action,
        )
        return connection.cursor()

    Node._get_database_cursor = classmethod(monkeypatched_get_cursor)
    try:
        yield None
    finally:
        Node._get_database_cursor = original_get_database_cursor


R = TypeVar("R")
P = ParamSpec("P")


def tree_mutex(classname: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to prevent treebeard from screwing up the database.
    Extending :func:`cache_based_lock`,
    we use :func:`django.db.transaction.atomic`
    and monkey patch :meth:`treebeard.models.Node._get_database_cursor`
    to actually use djangos database cursor and force it into db transactions that way.

    Allows page trees to be locked separately from POIs etc.,
    but requires strict conformance to always specify the exact ``classname`` when using the decorator.
    If there is a typo, there will be no indication at server startup, and collisions and data corruption may occur.
    For more information, see :func:`cache_based_lock`.
    """
    if classname not in _LOCKS:
        # Only one instance of lock per class is allowed to be functional
        _LOCKS[classname] = threading.RLock()
    lock = _LOCKS[classname]

    def wrap(func: Callable[P, R]) -> Callable[P, R]:
        """
        This is the actual decorator that takes ``func`` and returns a function with the same signature.
        The outer function :func:`tree_mutex` is necessary to get the ``classname`` variable.
        """

        @functools.wraps(func)
        def innermost_function(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The function replacing the decorated function.
            Invoke :func:`django.db.transaction.atomic`,
            monkey patch :meth:`treebeard.models.Node._get_database_cursor` to get djangos db cursor
            and finally call the decorated ``func``.
            """
            with (
                lock,
                transaction.atomic(using=DEFAULT_DB_ALIAS, durable=False),
                monkeypatch_cursor_func(using=DEFAULT_DB_ALIAS),
            ):
                return func(*args, **kwargs)

        return innermost_function

    return wrap
