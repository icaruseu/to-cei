"""Date parsing for `to_cei`.

`parse` is the public entry point — see its docstring for the full list
of accepted formats. The CEI/MOM-native format is `mom_date_to_time` /
`to_mom_date_value` (`YYYYMMDD`, with `99` denoting unknown month/day).
"""


import calendar
import re
from datetime import datetime
from typing import Callable, Union

from astropy.time import Time

__all__ = [
    "MOM_DATE_REGEX",
    "NO_DATE_VALUE",
    "NO_DATE_MARKERS",
    "ConventionParser",
    "is_no_date",
    "parse",
    "to_mom_date_value",
    "mom_date_to_time",
    "string_to_time",
    "extract_time",
]


# Archival "no date" markers, matched case-insensitively. The MOM
# `"99999999"` sentinel and the empty string are also treated as no-date
# by `is_no_date()` and `parse()`.
NO_DATE_MARKERS: frozenset[str] = frozenset(
    {
        # German
        "ohne datum",
        "o. d.",
        "o.d.",
        "od",
        "kein datum",
        "undatiert",
        # Latin (used across European archives)
        "sine dato",
        "sine die",
        "s. d.",
        "s.d.",
        "sd",
        # English
        "no date",
        "n. d.",
        "n.d.",
        "nd",
        "undated",
    }
)


def is_no_date(value: str) -> bool:
    """Return True if `value` is an archival "no date" marker.

    Recognises the entries in `NO_DATE_MARKERS`, the MOM ``"99999999"``
    sentinel, and the empty string. Case- and whitespace-insensitive.
    """
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    return not text or text == NO_DATE_VALUE or text in NO_DATE_MARKERS


# Convention parser protocol: takes a stripped, non-empty, non-no-date
# string; returns a `Time` / `(Time, Time)` or raises `ValueError` for
# "not my format". Both built-ins and user `extra_parsers` follow it.
ConventionParser = Callable[[str], Union[Time, tuple[Time, Time]]]

# Copied verbatim from the CEI schema's `normalizedDateValue` simple type.
# This is the schema's `@value` attribute format, not a parser-author choice
# — do not relax it. Note the year part has no leading-zero padding (year
# 769 is "769", not "0769"), so pre-1000 years use a 7-character form.
MOM_DATE_REGEX = re.compile(
    r"^(?P<year>-?[129]?[0-9][0-9][0-9])(?P<month>[019][0-9])(?P<day>[01239][0-9])$"
)
NO_DATE_VALUE = "99999999"

DateInput = (
    str
    | datetime
    | Time
    | tuple[str, str]
    | tuple[datetime, datetime]
    | tuple[Time, Time]
    | None
)
DateResult = Time | tuple[Time, Time] | None


def to_mom_date_value(time: Time) -> str:
    """Convert an `astropy.Time` into a MOM-compatible date string."""
    year, month, day = time.ymdhms[0], time.ymdhms[1], time.ymdhms[2]
    return "{year}{month}{day}".format(
        year=str(year).zfill(3) if year >= 0 else "-" + str(year * -1).zfill(3),
        month=str(month).zfill(2),
        day=str(day).zfill(2),
    )


def mom_date_to_time(value: str) -> Time | tuple[Time, Time]:
    """Convert a MOM date string into an `astropy.Time` or `(Time, Time)` range.

    Raises:
        ValueError: if the value is not a syntactically valid MOM date.
    """
    match = MOM_DATE_REGEX.search(value)
    if match is None:
        raise ValueError(
            f"Invalid MOM date {value!r}. Expected YYYYMMDD per CEI schema "
            f"(pattern -?[129]?[0-9][0-9][0-9][019][0-9][01239][0-9]); use "
            f"'99' for unknown month/day, '99999999' for fully unknown. "
            f"4-digit years must start with 1, 2, or 9 — use ISO 8601 for "
            f"others."
        )
    year = match.group("year")
    month = match.group("month")
    day = match.group("day")
    if month == "99":
        return (
            Time({"year": int(year), "month": 1, "day": 1}, format="ymdhms", scale="ut1"),
            Time({"year": int(year), "month": 12, "day": 31}, format="ymdhms", scale="ut1"),
        )
    if day == "99":
        return (
            Time(
                {"year": int(year), "month": int(month), "day": 1},
                format="ymdhms",
                scale="ut1",
            ),
            Time(
                {
                    "year": int(year),
                    "month": int(month),
                    "day": calendar.monthrange(int(year), int(month))[1],
                },
                format="ymdhms",
                scale="ut1",
            ),
        )
    return Time(
        {"year": int(year), "month": int(month), "day": int(day)},
        format="ymdhms",
        scale="ut1",
    )


def extract_time(time: Time | tuple[Time, Time]) -> Time:
    """Return the first time of a range, or the time itself if not a range."""
    return time[0] if isinstance(time, tuple) else time


def _looks_like_iso(value: str) -> bool:
    """Cheap pre-check: ISO dates have a hyphen at position 4."""
    if not value:
        return False
    head = value.lstrip("-")
    return len(head) >= 5 and head[4] == "-"


def string_to_time(value: str | tuple[str, str]) -> Time | tuple[Time, Time]:
    """Parse a date string (ISO or MOM) or a 2-tuple thereof into Time(s).

    Raises:
        ValueError: if the value cannot be parsed.
    """
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(f"Invalid date tuple provided: '{value}'")
        return (
            extract_time(string_to_time(value[0])),
            extract_time(string_to_time(value[1])),
        )
    if not isinstance(value, str) or not value:
        raise ValueError(f"Invalid date value: '{value!r}'")

    if _looks_like_iso(value):
        try:
            return Time(value, format="isot", scale="ut1")
        except ValueError as err:
            raise ValueError(
                f"Invalid ISO date string '{value}': {err}"
            ) from err
    return mom_date_to_time(value)


# Built-in convention parsers. Protocol: see `ConventionParser` above.

_DOTTED_DMY = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(-?\d{1,4})$")
_DOTTED_YMD = re.compile(r"^(-?\d{3,4})[.\-/](\d{1,2})[.\-/](\d{1,2})$")
_SLASH_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(-?\d{1,4})$")
_DOT_DMY_HYPHEN = re.compile(r"^(\d{1,2})-(\d{1,2})-(-?\d{1,4})$")  # rare DE
_YEAR_ONLY = re.compile(r"^(-?\d{1,4})$")

# German fuzzy patterns. Vocabulary is kept tight; anything not matched
# raises so the user notices and decides how to encode it.
_FUZZY_AROUND = re.compile(
    r"^(?:um|ca\.?|circa|gegen|etwa)\s+(-?\d{3,4})$", re.IGNORECASE
)
_FUZZY_OR = re.compile(r"^(-?\d{3,4})\s+oder\s+(-?\d{3,4})$", re.IGNORECASE)
_FUZZY_BETWEEN = re.compile(
    r"^zwischen\s+(-?\d{3,4})\s+und\s+(-?\d{3,4})$", re.IGNORECASE
)
_FUZZY_CENTURY = re.compile(
    r"^(?:(anfang|mitte|ende)\s+(?:des\s+)?)?(\d{1,2})\.\s*"
    r"(?:jh\.?|jahrhundert(?:s)?)$",
    re.IGNORECASE,
)


def _full_year(year: int) -> tuple[Time, Time]:
    return (
        Time({"year": year, "month": 1, "day": 1}, format="ymdhms", scale="ut1"),
        Time({"year": year, "month": 12, "day": 31}, format="ymdhms", scale="ut1"),
    )


def _exact(year: int, month: int, day: int) -> Time:
    return Time(
        {"year": year, "month": month, "day": day}, format="ymdhms", scale="ut1"
    )


def _try_iso(value: str) -> Time:
    if not _looks_like_iso(value):
        raise ValueError("not iso")
    try:
        return Time(value, format="isot", scale="ut1")
    except ValueError as err:
        raise ValueError(f"Invalid ISO date string '{value}': {err}") from err


def _try_mom(value: str) -> Time | tuple[Time, Time]:
    return mom_date_to_time(value)  # raises ValueError on mismatch


def _try_dotted(value: str) -> Time:
    """Dotted/slashed numeric formats: 15.03.1457, 1457.03.15, 15/03/1457, 15-03-1457."""
    m = _DOTTED_DMY.match(value) or _SLASH_DMY.match(value) or _DOT_DMY_HYPHEN.match(value)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _exact(year, month, day)
    m = _DOTTED_YMD.match(value)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _exact(year, month, day)
    raise ValueError("not dotted")


def _try_year(value: str) -> tuple[Time, Time]:
    """Bare 1-4 digit year → full-year range."""
    m = _YEAR_ONLY.match(value)
    if not m:
        raise ValueError("not year")
    return _full_year(int(m.group(1)))


def _try_german_fuzzy(value: str) -> tuple[Time, Time]:
    """German archival hedging: 'um 1457', 'zwischen X und Y', '15. Jh.', etc."""
    m = _FUZZY_AROUND.match(value)
    if m:
        return _full_year(int(m.group(1)))
    m = _FUZZY_OR.match(value)
    if m:
        a, b = sorted((int(m.group(1)), int(m.group(2))))
        return (_full_year(a)[0], _full_year(b)[1])
    m = _FUZZY_BETWEEN.match(value)
    if m:
        a, b = sorted((int(m.group(1)), int(m.group(2))))
        return (_full_year(a)[0], _full_year(b)[1])
    m = _FUZZY_CENTURY.match(value)
    if m:
        qualifier, century_str = m.group(1), m.group(2)
        century = int(century_str)
        first_year = (century - 1) * 100 + 1
        last_year = century * 100
        if qualifier:
            q = qualifier.lower()
            if q == "anfang":
                last_year = first_year + 32  # ~first third
            elif q == "mitte":
                first_year = first_year + 33
                last_year = first_year + 33
            elif q == "ende":
                first_year = last_year - 32
        return (_full_year(first_year)[0], _full_year(last_year)[1])
    raise ValueError("not german fuzzy")


# Built-in parsers in priority order. The parser tries them top-to-bottom
# and returns the first match. The labels are only used in error messages.
_BUILTIN_PARSERS: tuple[tuple[str, ConventionParser], ...] = (
    ("iso", _try_iso),
    ("mom", _try_mom),
    ("dotted", _try_dotted),
    ("year", _try_year),
    ("german_fuzzy", _try_german_fuzzy),
)


def _parse_string(
    value: str, extra_parsers: tuple[ConventionParser, ...]
) -> Time | tuple[Time, Time]:
    text = value.strip()
    if not text:
        raise ValueError("empty date string")
    errors: list[str] = []
    for label, parser in _BUILTIN_PARSERS:
        try:
            return parser(text)
        except ValueError as err:
            errors.append(f"{label}: {err}")
    for parser in extra_parsers:
        label = getattr(parser, "__name__", None) or repr(parser)
        try:
            return parser(text)
        except ValueError as err:
            errors.append(f"{label}: {err}")
    raise ValueError(
        f"Cannot parse date {value!r}. Tried: {'; '.join(errors)}"
    )


def parse(
    value: DateInput,
    *,
    extra_parsers: tuple[ConventionParser, ...] | list[ConventionParser] = (),
) -> DateResult:
    """Parse a date input into a `Time`, `(Time, Time)` range, or `None`.

    Real archival data routinely mixes complete dates with partial dates
    and "no date" markers. `parse` handles all three: it returns a `Time`
    for exact dates, a `(Time, Time)` range for partial ones (unknown
    day, year-only, "um 1457", century, etc.), and `None` for explicit
    no-date markers like `sine dato`. The built-in formats are tried in
    order and the first match wins.

    Pass-through / conversion:

    * `None` → `None`.
    * `astropy.time.Time` → returned as-is.
    * `datetime.datetime` → `Time` (UT1 scale).
    * `(from, to)` 2-tuple → explicit range. Both ends are taken
      literally; the MOM ``99`` expansion does not apply. If both ends
      are no-date markers the result is `None`.

    No-date markers (return `None`): empty string, MOM ``"99999999"``,
    and the entries in `NO_DATE_MARKERS` (Latin / German / English
    archival shorthands). See also `is_no_date()`.

    String formats, tried in order:

    1. **ISO 8601** — ``"1457-03-15"``.
    2. **MOM numeric** ``YYYYMMDD`` — ``"14570315"`` (exact),
       ``"14570399"`` (full-month range), ``"14579999"`` (full-year
       range). Schema-defined; 4-digit years must start with 1, 2, or 9.
    3. **Dotted/slashed numeric** — ``"15.03.1457"``, ``"1457.03.15"``,
       ``"15/03/1457"``, ``"15-03-1457"``.
    4. **Bare year** — ``"1457"`` → full-year range.
    5. **German archival fuzzy** — ``"um|ca.|circa|gegen|etwa 1457"``
       (full-year range), ``"1457 oder 1458"``, ``"zwischen X und Y"``,
       ``"15. Jahrhundert"`` / ``"15. Jh."``,
       ``"Anfang|Mitte|Ende des 15. Jahrhunderts"``.

    To handle a dialect the built-ins don't cover, pass a callable via
    `extra_parsers`. It receives a stripped, non-empty, non-no-date
    string and must return a `Time` / `(Time, Time)` or raise
    `ValueError` for "not my format". Extra parsers run after the
    built-ins::

        def julian_day(text: str) -> Time:
            if not text.startswith("JD"):
                raise ValueError("not a julian-day string")
            return Time(float(text[2:]), format="jd", scale="ut1")

        dates.parse("JD2451545.0", extra_parsers=[julian_day])

    Raises `ValueError` if no parser matches. The message lists every
    parser that was tried and why it rejected the input.
    """
    if value is None:
        return None
    if isinstance(value, Time):
        return value
    if isinstance(value, datetime):
        return Time(value, scale="ut1")
    extras = tuple(extra_parsers)
    if isinstance(value, str):
        if is_no_date(value):
            return None
        return _parse_string(value, extras)
    if isinstance(value, tuple) and len(value) == 2:
        a, b = value
        if isinstance(a, datetime) and isinstance(b, datetime):
            return (Time(a, scale="ut1"), Time(b, scale="ut1"))
        if isinstance(a, Time) and isinstance(b, Time):
            return (a, b)
        if isinstance(a, str) and isinstance(b, str):
            if is_no_date(a) and is_no_date(b):
                return None
            return (
                extract_time(_parse_string(a, extras)),
                extract_time(_parse_string(b, extras)),
            )
    raise ValueError(f"Cannot parse date value: {value!r}")
