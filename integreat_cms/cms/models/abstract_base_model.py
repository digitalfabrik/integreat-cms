from __future__ import annotations

import logging
from functools import cache
from typing import TYPE_CHECKING

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class SQLQueryNeverTriggered(Exception):
    """
    Placeholder for :class:`debug_toolbar.panels.sql.tracking.SQLQueryTriggered`
    when django-debug-toolbar is not installed
    """


@cache
def get_sql_query_triggered_exception() -> type[Exception]:
    """
    Returns the ``SQLQueryTriggered`` exception class raised by django-debug-toolbar
    when a query is triggered during ``repr()``.

    Imported lazily (and cached) because importing it at module level triggers the
    app registry since django-debug-toolbar 5.0. If the toolbar app is not installed
    (e.g. with ``DEBUG = False``), its models cannot be imported at all, so a
    placeholder exception class is returned instead.

    :return: The ``SQLQueryTriggered`` exception class
    """
    if not apps.is_installed("debug_toolbar"):
        return SQLQueryNeverTriggered

    from debug_toolbar.panels.sql.tracking import SQLQueryTriggered

    return SQLQueryTriggered


class AbstractBaseModel(models.Model):
    """
    Abstract base class for all models
    """

    @classmethod
    def get_model_name_plural(cls) -> str:
        """
        Get the plural representation of this model name

        :returns: The plural model name
        """
        model_name = cls._meta.model_name
        # Build correct plural of models ending with "y"
        return f"{model_name[:-1]}ies" if model_name.endswith("y") else f"{model_name}s"

    def get_repr(self) -> str:
        """
        Returns the canonical string representation of the content object

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return
        ``<AbstractContentModel: AbstractContentModel object (id)>``.
        It tries to get the representation of the inheriting model, but falls back to a minimal representation in case
        the fields used in the ``get_repr()`` method do not exist yet (e.g. because other errors occurred)

        :return: The canonical string representation of the content object
        """
        # Imported here because importing it at module level triggers the app registry
        # since django-debug-toolbar 5.0
        from debug_toolbar.panels.sql.tracking import SQLQueryTriggered

        try:
            return self.get_repr()
        except Exception as e:
            fallback_repr = f"<{type(self).__name__} (id: {self.id})>"
            # Skip logging if it's either a triggered SQL query or the id of the object is None and related objects do not exist yet
            if not (
                isinstance(e, get_sql_query_triggered_exception())
                or (isinstance(e, ObjectDoesNotExist) and not self.id)
            ):
                logger.debug(
                    "repr() for object %s failed because of %s: %s "
                    "(If you think this is no problem, please exclude this exception in the repr() method of the AbstractBaseModel.)",
                    fallback_repr,
                    type(e).__name__,
                    e,
                    exc_info=e,
                )
            return fallback_repr

    @classmethod
    def suggest(cls, **kwargs: Any) -> list[dict[str, Any]]:
        r"""
        Suggests keywords for searching the objects of the class

        :param \**kwargs: The supplied kwargs
        :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    class Meta:
        #: This model is an abstract base class
        abstract = True
