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
    uuid = uuid4()

    @wraps(func)
    def innermost_function(*args, **kwargs):
        lock_name = f"MUTEX_page_TREE"
        timeout = time.time() + LOCK_SECONDS
        while time.time() < timeout:
            # Attempt to acquire the mutex
            mutex = cache.get_or_set(lock_name, uuid, LOCK_SECONDS)
            # If our UUID was returned, we were successful!
            if mutex == uuid:
                # Run the actual function
                value = func(*args, **kwargs)
                # Release the mutex
                cache.delete(lock_name)
                return value
            else:
                time.sleep(interval)

    return innermost_function
