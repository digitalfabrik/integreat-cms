"""
This module contains a custom decorator for db / redis mutexes
"""

import time
from functools import wraps
from uuid import uuid4

from django.core.cache import cache

LOCK_SECONDS = 30
INTERVAL = 0.5


def tree_mutex(func):
    """
    define decorator that acts as a mutex
    """
    uuid = uuid4()

    @wraps(func)
    def innermost_function(*args, **kwargs):
        """
        mutex logic
        """
        # TODO: get name of model that is used with the mutex
        classname = "page"
        lock_name = f"MUTEX_{classname}_TREE"
        timeout = time.time() + LOCK_SECONDS
        while time.time() < timeout:
            if cache.get_or_set(lock_name, uuid, LOCK_SECONDS) == uuid:
                value = func(*args, **kwargs)
                cache.delete(lock_name)
                return value
            time.sleep(INTERVAL)
        raise TimeoutError("Failed to acquire {classname} lock")

    return innermost_function
