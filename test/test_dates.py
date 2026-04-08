from datetime import datetime

import pytest
from astropy.time import Time

from to_cei import dates


def test_parse_iso_string_returns_single_time():
    result = dates.parse("1457-03-15")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 1457
    assert result.ymdhms[1] == 3
    assert result.ymdhms[2] == 15


def test_parse_mom_exact_returns_single_time():
    result = dates.parse("14570315")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 1457


def test_parse_mom_unknown_day_returns_full_month_range():
    result = dates.parse("14570399")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[2] == 1
    assert result[1].ymdhms[2] == 31  # March has 31 days


def test_parse_mom_unknown_month_returns_full_year_range():
    result = dates.parse("14579999")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[1] == 1
    assert result[0].ymdhms[2] == 1
    assert result[1].ymdhms[1] == 12
    assert result[1].ymdhms[2] == 31


def test_parse_iso_tuple_returns_time_pair():
    result = dates.parse(("1457-03-15", "1457-03-20"))
    assert isinstance(result, tuple)
    assert result[0].ymdhms[2] == 15
    assert result[1].ymdhms[2] == 20


def test_parse_datetime():
    result = dates.parse(datetime(1457, 3, 15))
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 1457


def test_parse_datetime_tuple():
    result = dates.parse((datetime(1457, 3, 15), datetime(1457, 3, 20)))
    assert isinstance(result, tuple)
    assert result[0].ymdhms[2] == 15


def test_parse_time_returned_as_is():
    t = Time({"year": 1457, "month": 3, "day": 15}, format="ymdhms", scale="ut1")
    assert dates.parse(t) is t


def test_parse_iso_typo_raises_value_error():
    # Was historically swallowed and silently treated as MOM, masking the error.
    with pytest.raises(ValueError, match="Invalid ISO date"):
        dates.parse("1457-13-01")


def test_parse_empty_string_returns_none():
    # Empty string is treated as a "no date" marker, like sine dato.
    assert dates.parse("") is None


def test_parse_none_returns_none():
    assert dates.parse(None) is None


def test_parse_sine_dato_returns_none():
    assert dates.parse("sine dato") is None
    assert dates.parse("o.D.") is None
    assert dates.parse("99999999") is None


def test_parse_garbage_raises():
    with pytest.raises(ValueError):
        dates.parse("not a date")


def test_parse_negative_year_mom():
    # BCE year — regex permits leading minus.
    result = dates.parse("-4500315")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == -450


def test_parse_invalid_tuple_length():
    with pytest.raises(ValueError):
        dates.parse(("14570315",))  # type: ignore[arg-type]


def test_to_mom_date_value_roundtrip():
    t = dates.parse("14570315")
    assert isinstance(t, Time)
    assert dates.to_mom_date_value(t) == "14570315"


def test_extract_time_from_range():
    a, b = dates.parse("14570399")  # type: ignore[misc]
    assert dates.extract_time((a, b)) is a
    assert dates.extract_time(a) is a


# --------------------------------------------------------------------#
#                Convention parsers (parse extensions)                #
# --------------------------------------------------------------------#


def test_dotted_dmy_german_format():
    result = dates.parse("15.03.1457")
    assert isinstance(result, Time)
    assert (result.ymdhms[0], result.ymdhms[1], result.ymdhms[2]) == (1457, 3, 15)


def test_dotted_ymd_format():
    result = dates.parse("1457.03.15")
    assert isinstance(result, Time)
    assert (result.ymdhms[0], result.ymdhms[1], result.ymdhms[2]) == (1457, 3, 15)


def test_slash_dmy_format():
    result = dates.parse("15/03/1457")
    assert isinstance(result, Time)
    assert result.ymdhms[2] == 15


def test_year_only_returns_full_year_range():
    result = dates.parse("1457")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[1] == 1 and result[0].ymdhms[2] == 1
    assert result[1].ymdhms[1] == 12 and result[1].ymdhms[2] == 31


def test_german_fuzzy_um():
    result = dates.parse("um 1457")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1457
    assert result[1].ymdhms[0] == 1457


@pytest.mark.parametrize("text", ["ca. 1457", "circa 1457", "gegen 1457", "etwa 1457", "CA 1457"])
def test_german_fuzzy_around_variants(text):
    result = dates.parse(text)
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1457


def test_german_fuzzy_oder():
    result = dates.parse("1457 oder 1458")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1457
    assert result[0].ymdhms[1] == 1
    assert result[1].ymdhms[0] == 1458
    assert result[1].ymdhms[1] == 12


def test_german_fuzzy_zwischen():
    result = dates.parse("zwischen 1457 und 1460")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1457
    assert result[1].ymdhms[0] == 1460


def test_german_fuzzy_century():
    result = dates.parse("15. Jahrhundert")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1401
    assert result[1].ymdhms[0] == 1500


def test_german_fuzzy_century_short():
    result = dates.parse("15. Jh.")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1401
    assert result[1].ymdhms[0] == 1500


def test_german_fuzzy_century_anfang():
    result = dates.parse("Anfang des 15. Jahrhunderts")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 1401
    # Anfang covers ~first third → ends around 1433
    assert 1430 <= result[1].ymdhms[0] <= 1435


def test_iso_takes_precedence_over_year():
    # "1457-03-15" should match ISO, not year.
    result = dates.parse("1457-03-15")
    assert isinstance(result, Time)
    assert result.ymdhms[2] == 15


def test_unparseable_string_lists_every_attempt():
    with pytest.raises(ValueError, match="Tried:") as excinfo:
        dates.parse("nonsense gibberish")
    msg = str(excinfo.value)
    # Every built-in parser should be named in the error.
    for name in ("iso", "mom", "dotted", "year", "german_fuzzy"):
        assert name in msg


def test_dotted_in_tuple():
    result = dates.parse(("15.03.1457", "20.03.1457"))
    assert isinstance(result, tuple)
    assert result[0].ymdhms[2] == 15
    assert result[1].ymdhms[2] == 20


# --------------------------------------------------------------------#
#                       No-date markers                              #
# --------------------------------------------------------------------#


@pytest.mark.parametrize(
    "marker",
    [
        "sine dato",
        "Sine Dato",
        "s.d.",
        "s. d.",
        "sd",
        "sine die",
        "o.D.",
        "o. d.",
        "ohne Datum",
        "undatiert",
        "n.d.",
        "no date",
        "undated",
        "99999999",
        "",
        "   ",
    ],
)
def test_is_no_date_recognises_marker(marker):
    assert dates.is_no_date(marker)


@pytest.mark.parametrize("not_marker", ["1457", "1457-03-15", "um 1457", "abc"])
def test_is_no_date_rejects_real_dates(not_marker):
    assert not dates.is_no_date(not_marker)


def test_is_no_date_non_string_returns_false():
    assert not dates.is_no_date(None)  # type: ignore[arg-type]
    assert not dates.is_no_date(1457)  # type: ignore[arg-type]


def test_charter_date_value_accepts_sine_dato():
    from to_cei import Charter
    c = Charter("1", date_value="sine dato")
    assert c.date_value is None


def test_charter_date_value_accepts_ohne_datum():
    from to_cei import Charter
    c = Charter("1", date_value="ohne Datum")
    assert c.date_value is None


def test_charter_date_value_accepts_no_date_tuple():
    from to_cei import Charter
    c = Charter("1", date_value=("s.d.", "s.d."))
    assert c.date_value is None


# --------------------------------------------------------------------#
#                  User-supplied extra parsers                       #
# --------------------------------------------------------------------#


def test_extra_parser_handles_format_builtins_dont():
    def julian_day(text: str) -> Time:
        if not text.startswith("JD"):
            raise ValueError("not a julian-day string")
        return Time(float(text[2:]), format="jd", scale="ut1")

    result = dates.parse("JD2451545.0", extra_parsers=[julian_day])
    assert isinstance(result, Time)


def test_extra_parser_runs_after_builtins():
    # Built-ins handle "1457", so the extra parser must NOT see it.
    seen = []

    def trap(text: str) -> Time:
        seen.append(text)
        raise ValueError("not mine")

    dates.parse("1457", extra_parsers=[trap])
    assert seen == []  # built-in 'year' handled it first


def test_extra_parser_for_format_builtins_reject():
    def roman(text: str) -> Time:
        if text != "MCDLVII":
            raise ValueError("not roman")
        return Time(
            {"year": 1457, "month": 1, "day": 1}, format="ymdhms", scale="ut1"
        )

    result = dates.parse("MCDLVII", extra_parsers=[roman])
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 1457


def test_extra_parser_failure_listed_in_error():
    def always_fail(_: str) -> Time:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="always_fail: nope"):
        dates.parse("garbage gibberish", extra_parsers=[always_fail])


def test_extra_parsers_accepts_list_or_tuple():
    def passthrough(_: str) -> Time:
        return Time(
            {"year": 2000, "month": 1, "day": 1}, format="ymdhms", scale="ut1"
        )

    # Both list and tuple should work.
    assert dates.parse("xyz", extra_parsers=[passthrough]).ymdhms[0] == 2000
    assert dates.parse("xyz", extra_parsers=(passthrough,)).ymdhms[0] == 2000
