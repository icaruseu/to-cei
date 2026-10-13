import pytest
import requests
from xmlschema import XMLSchemaValidationError

from to_cei import validator
from to_cei.validator import CacheFetchError, Validator

EMPTY_XSD = (
    '<?xml version="1.0"?>'
    '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"></xs:schema>'
)


class FakeResponse:
    def __init__(self, text: str, status: int = 200, content_type: str = "text/plain"):
        self.text = text
        self.status_code = status
        self.ok = status < 400
        self.reason = "OK" if self.ok else "Not Found"
        self.headers = {"Content-Type": content_type}


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "_CACHE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def fetches(monkeypatch):
    """Records fetched URLs and answers with `fetches.response`, or raises it
    if it is an exception."""

    class Fetches(list):
        response: FakeResponse | Exception = FakeResponse(EMPTY_XSD)

    calls = Fetches()

    def fake_get(url, timeout):
        calls.append(url)
        if isinstance(calls.response, Exception):
            raise calls.response
        return calls.response

    monkeypatch.setattr(validator.requests, "get", fake_get)
    return calls


def test_no_exception_for_correct_cei(valid_cei):
    Validator().validate_cei(valid_cei)


def test_raises_exception_for_incorrect_cei(invalid_cei):
    with pytest.raises(XMLSchemaValidationError):
        Validator().validate_cei(invalid_cei)


def test_fetches_and_caches_missing_schema(cache_dir, fetches):
    Validator()
    assert len(fetches) == 1
    assert (cache_dir / "cei.xsd").read_text(encoding="utf-8") == EMPTY_XSD


def test_uses_cached_schema_without_fetching(cache_dir, fetches):
    (cache_dir / "cei.xsd").write_text(EMPTY_XSD, encoding="utf-8")
    Validator()
    assert fetches == []


def test_refetches_cached_schema_that_is_not_xml(cache_dir, fetches):
    (cache_dir / "cei.xsd").write_text("<html>Not Found</html>", encoding="utf-8")
    Validator()
    assert len(fetches) == 1
    assert (cache_dir / "cei.xsd").read_text(encoding="utf-8") == EMPTY_XSD


def test_refresh_fetches_despite_cached_schema(cache_dir, fetches):
    (cache_dir / "cei.xsd").write_text(EMPTY_XSD, encoding="utf-8")
    fetches.response = FakeResponse(EMPTY_XSD.replace("?>", "?><!-- new -->"))
    Validator(refresh=True)
    assert len(fetches) == 1
    assert "<!-- new -->" in (cache_dir / "cei.xsd").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse("<html>Not Found</html>", content_type="text/html"),
        FakeResponse("Not Found"),
        FakeResponse(EMPTY_XSD, status=404),
        requests.ConnectionError("offline"),
    ],
)
def test_failed_fetch_raises_and_caches_nothing(cache_dir, fetches, response):
    fetches.response = response
    with pytest.raises(CacheFetchError):
        Validator()
    assert not (cache_dir / "cei.xsd").exists()


def test_failed_refresh_keeps_cached_schema(cache_dir, fetches):
    (cache_dir / "cei.xsd").write_text(EMPTY_XSD, encoding="utf-8")
    fetches.response = requests.ConnectionError("offline")
    with pytest.raises(CacheFetchError):
        Validator(refresh=True)
    assert (cache_dir / "cei.xsd").read_text(encoding="utf-8") == EMPTY_XSD


def test_fetch_leaves_only_the_complete_cache_file(cache_dir, fetches):
    Validator()
    assert [path.name for path in cache_dir.iterdir()] == ["cei.xsd"]


def test_refetches_cached_schema_that_is_not_utf8(cache_dir, fetches):
    (cache_dir / "cei.xsd").write_bytes(b"\xff\xfe<xs:schema")
    Validator()
    assert len(fetches) == 1
    assert (cache_dir / "cei.xsd").read_text(encoding="utf-8") == EMPTY_XSD


def test_uses_fetched_schema_when_cache_cannot_be_written(
    tmp_path, monkeypatch, fetches
):
    blocked = tmp_path / "file"
    blocked.write_text("not a folder", encoding="utf-8")
    monkeypatch.setattr(validator, "_CACHE_DIR", blocked / "to-cei")
    with pytest.warns(UserWarning, match="could not cache"):
        Validator()
    assert len(fetches) == 1


def test_failed_cache_write_leaves_no_partial_file(cache_dir, fetches, monkeypatch):
    def fail(self, target):
        raise OSError("disk full")

    monkeypatch.setattr(validator.Path, "replace", fail)
    with pytest.warns(UserWarning, match="disk full"):
        Validator()
    assert list(cache_dir.iterdir()) == []
