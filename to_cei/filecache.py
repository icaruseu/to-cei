"""On-disk cache for fetched XML resources (the CEI XSD).

Stores response bodies in a `shelve` under ``~/.cache/to-cei/cache`` and
refuses to cache anything that doesn't look like XML, so an HTML error
page can't silently poison the cache.
"""


from __future__ import annotations

import atexit
import os
import shelve
from pathlib import Path

import requests


class CacheFetchError(RuntimeError):
    """Raised when a remote fetch cannot be turned into a usable cache entry."""


def _looks_like_xml(body: str) -> bool:
    """Cheap content sniff for XML/XSD bodies."""
    if not body:
        return False
    head = body.lstrip()[:512].lower()
    if head.startswith("<?xml"):
        return True
    # Tolerate XSDs without an XML declaration.
    return "<xs:schema" in head or '<schema xmlns="http://www.w3.org/2001/xmlschema"' in head


class FileCache:
    __shelf: shelve.Shelf
    __session: requests.Session

    def __init__(self, base: str = str(Path.home().joinpath(".cache", "to-cei"))):
        os.makedirs(base, exist_ok=True)
        self.__shelf = shelve.open(os.path.join(base, "cache"), writeback=True)
        self.__session = requests.Session()
        atexit.register(self.close)

    def __enter__(self) -> FileCache:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        try:
            self.__shelf.close()
        except Exception:
            pass
        try:
            self.__session.close()
        except Exception:
            pass

    def get(self, url: str, force: bool = False) -> str:
        """Return the cached body for `url`, fetching it if needed.

        Raises `CacheFetchError` if the fetch fails or the response
        doesn't look like XML. Cached entries that fail the XML sniff
        are treated as a miss and re-fetched (one-shot self-healing for
        previously-poisoned caches).
        """
        cached = self.__shelf.get(url) if not force else None
        if isinstance(cached, str) and _looks_like_xml(cached):
            return cached

        try:
            response = self.__session.get(url, timeout=30, allow_redirects=True)
        except requests.RequestException as err:
            raise CacheFetchError(f"failed to fetch {url}: {err}") from err

        if not response.ok:
            raise CacheFetchError(
                f"failed to fetch {url}: HTTP {response.status_code} {response.reason}"
            )

        content_type = response.headers.get("Content-Type", "").lower()
        body = response.text

        if "html" in content_type or not _looks_like_xml(body):
            raise CacheFetchError(
                f"refusing to cache {url}: response is not XML "
                f"(Content-Type={content_type!r})"
            )

        self.__shelf[url] = body
        self.__shelf.sync()
        return body
