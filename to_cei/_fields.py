"""Declarative field descriptor for `Charter`.

Each `CharterField` declaration replaces a property/setter/private-storage
triple. Storage is per-instance under ``_<name>`` (no shared mutable
defaults), and the `normalize` callable runs on every assignment — and
on first read of an unset field, so callers always see the canonical
empty value (e.g. ``[]`` for list fields).
"""

from __future__ import annotations

from typing import Any, Callable


class CharterField:
    __slots__ = ("normalize", "private_name", "public_name")

    def __init__(self, normalize: Callable[[Any], Any]) -> None:
        self.normalize = normalize
        self.public_name = ""
        self.private_name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        try:
            return instance.__dict__[self.private_name]
        except KeyError:
            value = self.normalize(None)
            instance.__dict__[self.private_name] = value
            return value

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.private_name] = self.normalize(value)
