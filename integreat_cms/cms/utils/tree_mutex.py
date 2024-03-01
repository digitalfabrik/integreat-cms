"""
This module contains a custom decorator for db / redis mutexes
"""

import time
from functools import wraps
from uuid import uuid4

from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, transaction
from treebeard.models import Node

LOCK_SECONDS = 10
INTERVAL = 0.5

def build_monkeypatched_cursor_func(using=DEFAULT_DB_ALIAS):
    connection = transaction.get_connection(using=using)
    def get_monkeypatch_cursor(cls, action):
        print(f"someone is getting our monkeypatched cursor ({using})! {cls}, {action}")
        return connection.cursor()
    return get_monkeypatch_cursor

get_old_cursor_func = Node._get_database_cursor


def tree_mutex(func):
    """
    define decorator that acts as a mutex
    """

    @wraps(func)
    def innermost_function(*args, **kwargs):
        """
        mutex logic
        """
        # TODO: get name of model that is used with the mutex
        classname = "page"
        lock_name = f"MUTEX_{classname}_TREE"
        uuid = uuid4()
        timeout = time.time() + LOCK_SECONDS
        while time.time() < timeout:
            if cache.get_or_set(lock_name, uuid, LOCK_SECONDS) == uuid:
                print(f"  Acquired {lock_name} as {uuid}.")
                # Use not as decorator but as context manager so we can make sure the same identifier is used by treebeard
                with transaction.atomic(using=DEFAULT_DB_ALIAS, durable=True):
                    old_cursor_func = Node._get_database_cursor
                    # Patch treebeard database cursor
                    Node._get_database_cursor = build_monkeypatched_cursor_func(DEFAULT_DB_ALIAS)
                    # Run the actual function
                    value = func(*args, **kwargs)
                    # Restore old cursor function
                    Node._get_database_cursor = old_cursor_func
                    #Node._get_database_cursor = get_old_cursor_func
                    # Release the mutex
                    print(f"  Releasing {lock_name} ({uuid})")
                    cache.delete(lock_name)
                    return value
            else:
                print(f"  Failed to acquire {lock_name} as {uuid}: {mutex} present. Waiting {INTERVAL}s…")
                time.sleep(INTERVAL)
        raise TimeoutError("Failed to acquire {classname} lock")

    return innermost_function
