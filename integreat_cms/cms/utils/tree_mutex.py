"""
This module contains a custom decorator for db / redis mutexes
"""

import functools
import logging
import threading
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from django.db import DEFAULT_DB_ALIAS, transaction

logger = logging.getLogger(__name__)

#: For how many seconds the lock persists, and the timeout for retrying to acquire it.
LOCK_SECONDS = 10
#: How long to sleep between retries to acquire the lock.
INTERVAL = 0.1


#: A dictionary holding separate locks for each classname to be guarded
_LOCKS: dict[str, threading.RLock] = {}


R = TypeVar("R")
P = ParamSpec("P")


def tree_mutex(classname: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to prevent treebeard from screwing up the database.
    Extending :func:`cache_based_lock`,
    we use :func:`django.db.transaction.atomic`
    to force treebeard's tree operations into a database transaction.

    Allows page trees to be locked separately from places etc.,
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
            Invoke :func:`django.db.transaction.atomic`
            and call the decorated ``func`` while holding the lock.
            """
            with (
                lock,
                transaction.atomic(using=DEFAULT_DB_ALIAS, durable=False),
            ):
                return func(*args, **kwargs)

        return innermost_function

    return wrap
