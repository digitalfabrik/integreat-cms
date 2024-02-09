"""
This file contains a mechanism to lock a content editor for other people while a person is using it.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.cache import cache

if TYPE_CHECKING:
    from typing import Final

    from ..models import User

logger = logging.getLogger(__name__)


LOCKED_PAGE_PREFIX: Final[str] = "cms_content_edit_lock"
LOCK_TIMEOUT_SECONDS: Final[int] = 90


def get_locking_user(id_: int | str | None, type_: str) -> User | None:
    """
    This function returns the user that locks a specific object

    :param id_: The id of the content object or None
    :param type_: The type of the content object
    :return: The user that holds the lock for this content object or None
    """
    if id_ is None:
        return None

    cache_key = get_cache_key(id_, type_)
    return cache.get(cache_key)


def lock_content(id_: int | None, type_: str, user: User) -> bool:
    """
    This function tries to lock a content object for a user.
    If it is already locked by someone else, nothing will happen.
    If it is already locked by the same user, the timeout gets reset.

    :param id_: The id of the content object or None
    :param type_: The type of the content object
    :param user: The user that should get unique access to this content object
    :return: Whether the content object could be locked
    """
    if id_ is None:
        return False

    cache_key = get_cache_key(id_, type_)

    locking_user = get_locking_user(id_, type_)
    if locking_user is not None and locking_user != user:
        return False

    cache.set(cache_key, user, timeout=LOCK_TIMEOUT_SECONDS)

    if locking_user is None:
        logger.debug("Locked %s with id %s by %r", type_, id_, user)
    else:
        logger.debug("Extended lock for %s with id %s by %r", type_, id_, user)

    return True


def unlock_content(id_: int | None, type_: str, user: User) -> bool:
    """
    This function tries to unlock a content object for a user.
    If it is not locked by the passed user, nothing will happen.

    :param id_: The id of the content object or None
    :param type_: The type of the content object
    :param user: The user that wants to release the lock
    :return: Whether the content object could be unlocked
    """
    if id_ is None:
        return False

    cache_key = get_cache_key(id_, type_)

    locking_user = get_locking_user(id_, type_)
    if locking_user is None or locking_user != user:
        return False

    cache.delete(cache_key)

    logger.debug("Explicitly unlocked %s with id %s by %r", type_, id_, user)

    return True


def get_cache_key(id_: int | str, type_: str) -> str:
    """
    This function returns the key that is used to lock a content object in the cache.
    It should not be used outside of this module.

    :param id_: The id of the content object
    :param type_: The type of the content object
    :return: The key to use
    """
    return f"{LOCKED_PAGE_PREFIX}_{type_}_{id_}"
