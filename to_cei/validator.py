"""CEI schema validation. The XSD is loaded once per `Validator` instance."""

import os
import tempfile
import warnings
from pathlib import Path
from typing import Any

import requests
import xmlschema
from lxml import etree

from to_cei import config

_CACHE_DIR = Path.home() / ".cache" / "to-cei"


class CacheFetchError(RuntimeError):
    """Raised when the CEI schema cannot be fetched."""


def _looks_like_xml(body: str) -> bool:
    """Cheap content sniff for XML/XSD bodies."""
    if not body:
        return False
    head = body.lstrip()[:512].lower()
    if head.startswith("<?xml"):
        return True
    # Tolerate XSDs without an XML declaration.
    return (
        "<xs:schema" in head
        or '<schema xmlns="http://www.w3.org/2001/xmlschema"' in head
    )


def _load_schema(refresh: bool) -> str:
    """Return the CEI XSD from the disk cache, fetching it if needed.

    A cached copy that can't be read or doesn't look like XML counts as
    missing. A response that doesn't look like XML is refused, so an HTML
    error page can't end up in the cache. If the cache can't be written,
    the fetched schema is still used.
    """
    url = config.CEI_SCHEMA_URL
    path = _CACHE_DIR / "cei.xsd"
    if not refresh:
        try:
            cached = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            cached = ""
        if _looks_like_xml(cached):
            return cached

    try:
        response = requests.get(url, timeout=30)
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

    try:
        _write_cache(path, body)
    except OSError as err:
        warnings.warn(f"could not cache the CEI schema in {path}: {err}", stacklevel=3)
    return body


def _write_cache(path: Path, body: str) -> None:
    # A cut-off file would still pass the XML check, so the cache file is
    # only replaced once the new one is complete.
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as partial:
            partial.write(body)
        Path(name).replace(path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


class Validator:
    _schema: xmlschema.XMLSchema11

    def __init__(self, refresh: bool = False) -> None:
        """Loads the CEI schema, from the disk cache if possible.

        Args:
            refresh: If True, fetch the schema from the mom-ca repository
                even if a cached copy exists, and replace the cached copy.

        Raises:
            CacheFetchError: if the schema has to be fetched and the fetch fails.
        """
        self._schema = xmlschema.XMLSchema11(_load_schema(refresh))

    def validate_cei(self, element: etree._Element) -> None:
        """Validate `element` against the CEI schema.

        Raises `xmlschema.XMLSchemaValidationError` on failure.
        """
        resource: Any = element
        self._schema.validate(resource)

    def is_valid_cei(self, element: etree._Element) -> bool:
        """Non-raising variant of `validate_cei`."""
        resource: Any = element
        return self._schema.is_valid(resource)
