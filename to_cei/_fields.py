"""Declarative field descriptor.

Each `Field` declaration replaces a property/setter/private-storage
triple. Storage is per-instance under ``_<name>`` (no shared mutable
defaults), and the `normalize` callable runs on every assignment and on
the first read of an unset field, so callers always see the canonical
empty value (e.g. ``[]`` for list fields).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self, overload


class Field[T]:
    __slots__ = ("normalize", "private_name", "public_name")

    def __init__(self, normalize: Callable[[Any], T]) -> None:
        self.normalize = normalize
        self.public_name = ""
        self.private_name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> T: ...

    def __get__(self, instance: object, owner: type | None = None) -> Self | T:
        if instance is None:
            return self
        try:
            return instance.__dict__[self.private_name]
        except KeyError:
            value = self.normalize(None)
            instance.__dict__[self.private_name] = value
            return value

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.private_name] = self._normalized(value)

    def _normalized(self, value: Any) -> T:
        try:
            return self.normalize(value)
        except (TypeError, ValueError) as err:
            # A subclass such as UnicodeDecodeError takes other arguments, so
            # the error is raised again as its base class.
            kind = TypeError if isinstance(err, TypeError) else ValueError
            raise kind(f"{self.public_name}: {err}") from err


def check_fields(instance: object) -> None:
    """Checks every field of `instance` again, so a value changed in place,
    such as a list a caller appended to, meets the rules of an assignment."""
    for cls in type(instance).__mro__:
        for field in vars(cls).values():
            if isinstance(field, Field) and field.private_name in instance.__dict__:
                field._normalized(instance.__dict__[field.private_name])
