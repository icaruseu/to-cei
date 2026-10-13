"""Date parsing for `to_cei`.

`parse` turns the date forms found in archival data into a `MomDate`, a
`(MomDate, MomDate)` range or `None`. See its docstring for the accepted
forms. `to_mom_date_value` writes the CEI/MOM value form (`YYYYMMDD`).

Years before 1000 have no leading zero in the MOM form: year 769 is
``"7690101"``, not ``"07690101"``, which the CEI schema rejects. Years
below 100 still need three digits there, so year 12 is ``"0121211"``.
ISO and dotted forms accept padded and unpadded years, but a short
unpadded form is ambiguous: ``"12.12.11"`` parses as day 12, month 12,
year 11, because a year-first form needs at least three year digits.
Fully padded forms such as ``"0012-12-11"`` avoid that.
"""

import numbers
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

__all__ = [
    "MOM_DATE_REGEX",
    "NO_DATE_VALUE",
    "ConventionParser",
    "DateInput",
    "MomDate",
    "is_no_date",
    "parse",
    "to_mom_date_value",
]

_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _days_in_month(year: int, month: int) -> int:
    if month == 2 and year % 4 == 0:
        return 29
    return _MONTH_DAYS[month - 1]


@dataclass(frozen=True, order=True)
class MomDate:
    """A calendar date of a charter.

    Years count astronomically, so year 0 is 1 BCE and year -450 is
    451 BCE.

    The day is checked against the Julian leap rule, so every year
    divisible by 4 has a 29 February, including 1300, 1700 and 1900.
    Resolved charter dates follow the calendar in force where the
    charter was issued, which is the Julian calendar before the local
    calendar reform, in some territories long after 1582. A 29 February
    of a Julian leap year is therefore a valid date in any century. The
    check accepts every date that is valid in either calendar, so it
    doesn't catch a 29 February given for a Gregorian common year.

    Raises:
        TypeError: if a part isn't an integer.
        ValueError: if the month or day does not exist.
    """

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        for name in ("year", "month", "day"):
            part = getattr(self, name)
            if not isinstance(part, numbers.Integral) or isinstance(part, bool):
                raise TypeError(f"{name} must be an integer, got {type(part).__name__}")
            # An integer from numpy or pandas is stored as a plain int.
            object.__setattr__(self, name, int(part))
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month {self.month} is out of range")
        days = _days_in_month(self.year, self.month)
        if not 1 <= self.day <= days:
            raise ValueError(
                f"Day {self.day} is out of range for {self.year}-{self.month:02d}"
            )

    def isoformat(self) -> str:
        """Return the date as `1457-03-15`, `0769-01-15` or `-0450-03-15`."""
        sign = "-" if self.year < 0 else ""
        return f"{sign}{abs(self.year):04d}-{self.month:02d}-{self.day:02d}"


def is_no_date(value: str) -> bool:
    """Return True if `value` is empty, only whitespace, or the MOM
    no-date value ``"99999999"``."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    return not text or text == NO_DATE_VALUE


ConventionParser = Callable[[str], MomDate | tuple[MomDate, MomDate]]

# The CEI schema's `normalizedDateValue` type, the format of `@value`.
MOM_DATE_REGEX = re.compile(
    r"^(?P<year>-?[129]?[0-9][0-9][0-9])(?P<month>[019][0-9])(?P<day>[01239][0-9])$"
)
NO_DATE_VALUE = "99999999"

type SingleDate = str | date | MomDate
type DateInput = SingleDate | tuple[SingleDate, SingleDate] | None
DateResult = MomDate | tuple[MomDate, MomDate] | None


def to_mom_date_value(time: MomDate) -> str:
    """Return the MOM value form of a date, such as `"14570315"`.

    Raises:
        ValueError: if the CEI schema has no value form for the year, which
            is the case for the years 3000 to 8999, -3000 to -8999 and
            beyond 9999 in either direction.
    """
    year = str(abs(time.year)).zfill(3)
    value = f"{'-' if time.year < 0 else ''}{year}{time.month:02d}{time.day:02d}"
    if not MOM_DATE_REGEX.fullmatch(value):
        raise ValueError(f"The year {time.year} has no MOM value form")
    return value


def _try_mom(value: str) -> MomDate | tuple[MomDate, MomDate]:
    """The MOM value form. A `99` for an unknown month or day gives a range."""
    match = MOM_DATE_REGEX.search(value)
    if match is None:
        raise ValueError(
            f"Invalid MOM date {value!r}. Expected YYYYMMDD per CEI schema "
            f"(pattern -?[129]?[0-9][0-9][0-9][019][0-9][01239][0-9]); use "
            f"'99' for unknown month/day, '99999999' for fully unknown. "
            f"4-digit years must start with 1, 2, or 9 — use ISO 8601 for "
            f"others."
        )
    year = int(match.group("year"))
    month = match.group("month")
    day = match.group("day")
    if month == "99":
        return _full_year(year)
    if day == "99":
        return (
            MomDate(year, int(month), 1),
            MomDate(year, int(month), _days_in_month(year, int(month))),
        )
    return MomDate(year, int(month), int(day))


def _looks_like_iso(value: str) -> bool:
    """Whether `value` has a hyphen after four year digits, as an ISO date has."""
    if not value:
        return False
    head = value.lstrip("-")
    return len(head) >= 5 and head[4] == "-"


_ISO = re.compile(
    r"(-?\d{4})-(\d{1,2})-(\d{1,2})"
    r"(?:T(\d{1,2}):(\d{1,2})(?::(\d{1,2})(?:\.\d+)?)?)?"
)
_DOTTED_DMY = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(-?\d{1,4})$")
_DOTTED_YMD = re.compile(r"^(-?\d{3,4})[.\-/](\d{1,2})[.\-/](\d{1,2})$")
_SLASH_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(-?\d{1,4})$")
_DOT_DMY_HYPHEN = re.compile(r"^(\d{1,2})-(\d{1,2})-(-?\d{1,4})$")
_YEAR_ONLY = re.compile(r"^(-?\d{1,4})$")


def _full_year(year: int) -> tuple[MomDate, MomDate]:
    return (MomDate(year, 1, 1), MomDate(year, 12, 31))


def _try_iso(value: str) -> MomDate:
    """ISO 8601 date, optionally followed by T and a time of day without a time
    zone, which is dropped."""
    if not _looks_like_iso(value):
        raise ValueError("not iso")
    m = _ISO.fullmatch(value)
    if m is None:
        raise ValueError(f"Invalid ISO date string '{value}'")
    year, month, day, hour, minute, second = m.groups()
    if hour is not None and (
        int(hour) > 23 or int(minute) > 59 or int(second or 0) > 60
    ):
        raise ValueError(f"Invalid ISO date string '{value}': time out of range")
    try:
        return MomDate(int(year), int(month), int(day))
    except ValueError as err:
        raise ValueError(f"Invalid ISO date string '{value}': {err}") from err


def _try_dotted(value: str) -> MomDate:
    """Dotted/slashed numeric: 15.03.1457, 1457.03.15, 15/03/1457, 15-03-1457."""
    m = (
        _DOTTED_DMY.match(value)
        or _SLASH_DMY.match(value)
        or _DOT_DMY_HYPHEN.match(value)
    )
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return MomDate(year, month, day)
    m = _DOTTED_YMD.match(value)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return MomDate(year, month, day)
    raise ValueError("not dotted")


def _try_year(value: str) -> tuple[MomDate, MomDate]:
    """A bare year of one to four digits, as a full-year range."""
    m = _YEAR_ONLY.match(value)
    if not m:
        raise ValueError("not year")
    return _full_year(int(m.group(1)))


# Built-in parsers in priority order. The labels are only used in error
# messages.
_BUILTIN_PARSERS: tuple[tuple[str, ConventionParser], ...] = (
    ("iso", _try_iso),
    ("mom", _try_mom),
    ("dotted", _try_dotted),
    ("year", _try_year),
)


def _parse_string(
    value: str, extra_parsers: tuple[ConventionParser, ...]
) -> MomDate | tuple[MomDate, MomDate]:
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
            result = parser(text)
        except ValueError as err:
            errors.append(f"{label}: {err}")
            continue
        return _checked(result, label)
    raise ValueError(f"Cannot parse date {value!r}. Tried: {'; '.join(errors)}")


def _checked(result: object, label: str) -> MomDate | tuple[MomDate, MomDate]:
    """The result of an extra parser, if it's a `MomDate` or a range."""
    if isinstance(result, MomDate):
        return result
    if (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[0], MomDate)
        and isinstance(result[1], MomDate)
    ):
        return _range(result[0], result[1])
    raise ValueError(
        f"{label} returned {result!r}, not a MomDate or a (start, end) range"
    )


def _parse_single(
    value: SingleDate | None, extras: tuple[ConventionParser, ...]
) -> DateResult:
    if value is None:
        return None
    if isinstance(value, MomDate):
        return value
    if isinstance(value, date):
        return MomDate(value.year, value.month, value.day)
    if isinstance(value, str):
        return None if is_no_date(value) else _parse_string(value, extras)
    raise TypeError(f"expected text, a date or a MomDate, got {type(value).__name__}")


def _range(
    start: MomDate | tuple[MomDate, MomDate], end: MomDate | tuple[MomDate, MomDate]
) -> MomDate | tuple[MomDate, MomDate]:
    """An explicit range from the first day of `start` to the last day of
    `end`, or a single date if both are the same day."""
    first = start[0] if isinstance(start, tuple) else start
    last = end[1] if isinstance(end, tuple) else end
    if first > last:
        raise ValueError(
            f"A date range must not end before it starts: "
            f"{first.isoformat()} – {last.isoformat()}"
        )
    return first if first == last else (first, last)


def parse(
    value: DateInput,
    *,
    extra_parsers: tuple[ConventionParser, ...] | list[ConventionParser] = (),
) -> DateResult:
    """Parse a date input into a `MomDate`, a `(MomDate, MomDate)` range or `None`.

    `parse` returns a `MomDate` for an exact date, a range for a period
    such as a year or a month with an unknown day, and `None` for no date.
    It reads only forms that don't depend on a language. Expressions in a
    natural language ("um 1457", "15. Jh.", "20. September 1246") need a
    parser in `extra_parsers`, and a project maps its no-date markers
    ("sine dato", "o. D.") to `None` before calling `parse`.

    Inputs other than text:

    * `None` stays `None`, and a `MomDate` is returned unchanged.
    * A `datetime.date` or `datetime.datetime` becomes a `MomDate`, and
      the time of day is dropped.
    * A `(start, end)` tuple of single forms is an explicit range from
      the first day of `start` to the last day of `end`, so
      ``("1457", "1460")`` covers 1457-01-01 to 1460-12-31. A range whose
      ends are the same day becomes that single `MomDate`, and a range
      that ends before it starts raises `ValueError`. If both ends are no
      date, the result is `None`, and if only one is, `parse` raises
      `ValueError`.

    An empty or whitespace-only string and the MOM value ``"99999999"``
    mean no date, as `is_no_date` checks.

    Text forms, tried in this order until one matches:

    1. An ISO 8601 date, ``"1457-03-15"``, optionally followed by ``T``
       and a time of day without a time zone (``"1457-03-15T12:00:00"``),
       which is dropped.
    2. The MOM value form ``YYYYMMDD``: ``"14570315"`` for a day,
       ``"14570399"`` for a month and ``"14579999"`` for a year. A
       four-digit year starts with 1, 2 or 9, as the CEI schema requires.
    3. Numeric dates with dots, slashes or hyphens: ``"15.03.1457"``,
       ``"1457.03.15"``, ``"15/03/1457"``, ``"15-03-1457"``.
    4. A bare year such as ``"1457"``, as a full-year range.

    A callable in `extra_parsers` handles a form the built-in parsers
    don't cover. It runs after them and receives a stripped, non-empty
    string that isn't a no-date value. It returns a `MomDate` or a
    `(start, end)` range, or raises `ValueError` if the string isn't its
    format::

        def anno_domini(text: str) -> tuple[MomDate, MomDate]:
            m = re.fullmatch(r"anno domini (\\d{3,4})", text, re.IGNORECASE)
            if m is None:
                raise ValueError("not an 'anno domini' year")
            year = int(m.group(1))
            return (MomDate(year, 1, 1), MomDate(year, 12, 31))

        dates.parse("anno domini 1457", extra_parsers=[anno_domini])

    Raises:
        TypeError: if `value` or an end of a range isn't text, a `date` or
            a `MomDate`.
        ValueError: if no parser matches, with every parser tried and its
            reason, or if an extra parser returns something other than a
            `MomDate` or a range that doesn't end before it starts.
    """
    extras = tuple(extra_parsers)
    if not isinstance(value, tuple):
        return _parse_single(value, extras)
    if len(value) != 2:
        raise ValueError(f"A date range needs exactly two ends: {value!r}")
    start = _parse_single(value[0], extras)
    end = _parse_single(value[1], extras)
    if start is None and end is None:
        return None
    if start is None or end is None:
        raise ValueError(f"A date range needs both ends or neither: {value!r}")
    return _range(start, end)
