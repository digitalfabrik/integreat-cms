"""
This module contains utilities to repair or detect inconsistencies in a tree
"""

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from django.db.models import Model

T = TypeVar("T", bound=Model)


class ShadowInstance(Generic[T]):
    """
    An object shadowing the attributes of the model instance passed to it on instantiation
    and withholding any attribute changes until explicitly applied,
    allowing to compare the old and new states before committing to them.
    """

    def __init__(self, instance: T):
        self._instance = instance
        self._overrides: dict[str, dict[str, Any]] = {}

    @property
    def instance(self) -> T:
        """
        Return the shadowed instance.
        """
        return self._instance

    def discard_changes(self, attributes: Iterable | None = None) -> None:
        """
        Discard changes of the listed attributes.
        Discards all changes if ``attributes`` is ``None``.
        """
        if attributes is None:
            attributes = self._overrides.keys()
        for name in attributes:
            del self._overrides[name]

    def apply_changes(self, attributes: Iterable | None = None) -> None:
        """
        Apply changes of the listed attributes.
        Applies all changes if ``attributes`` is ``None``.
        """
        if attributes is None:
            attributes = self._overrides.keys()
        for name, value in self._overrides.items():
            if name in attributes:
                setattr(self._instance, name, value)

    @property
    def changed_attributes(self) -> dict[str, dict[str, Any]]:
        """
        A dictionary of all attributes whose value is to be changed.
        The value to each attribute name is another dictionary containing the ``"old"`` and ``"new"`` value.

        Note that this does not show attributes that were overwritten with the same value (so display no difference yet) –
        for this see :attr:`overwritten_attributes`.
        """
        return {
            name: values
            for name, values in self.overwritten_attributes.items()
            if "old" not in values or values["old"] != values["new"]
        }

    @property
    def overwritten_attributes(self) -> dict[str, dict[str, Any]]:
        """
        A dictionary of all overwritten attributes.
        The value to each attribute name is another dictionary containing the ``"old"`` and ``"new"`` value
        (missing the ``"old"`` value if the attribute is not set on the :attr:`instance`).

        Note that this even shows attributes that were overwritten with the same value (so display no difference yet) –
        for only the changed values see :attr:`changed_attributes`.
        """
        return {
            name: {"new": value}
            | (
                {"old": getattr(self._instance, name)}
                if name in dir(self._instance)
                else {}
            )
            for name, value in self._overrides.items()
        }

    def save(self, *args: list, **kwargs: dict) -> None:
        """
        Save the shadowed instance.
        Does nothing if no changes were applied yet (see :meth:`apply_changes`).
        """
        self._instance.save(*args, **kwargs)

    def reload(self) -> None:
        """
        Reload the shadowed instance from the database.
        The state of the overwritten attributes is kept.

        This can be used to incorporate recent changes to the database object after a longer (i.e. user directed) staging period.
        """
        self._instance = type(self._instance).objects.get(id=self._instance.pk)

    def __getattribute__(self, name: str) -> Any:
        """
        If there's not anything important of ``self`` requested, return the staged new value for the attribute of the :attr:`instance`.
        If it is not found or ends in ``__original``, return the value of the actual attribute.
        """
        if name.startswith("_") or name in {
            "discard_changes",
            "apply_changes",
            "changed_attributes",
            "overwritten_attributes",
            "save",
            "reload",
            "instance",
        }:
            return super().__getattribute__(name)
        if name in self._overrides and not name.endswith("__original"):
            return self._overrides[name]
        return getattr(self._instance, name.removesuffix("__original"))

    def __setattr__(self, name: str, value: Any) -> None:
        """
        If there's not anything important of ``self`` requested, stage the new value as an override for the attribute of the :attr:`instance`.
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._overrides[name] = value
