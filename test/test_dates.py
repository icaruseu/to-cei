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


# --------------------------------------------------------------------#
#               Schema-edge years: pre-1000, BCE, boundaries          #
# --------------------------------------------------------------------#
#
# The CEI schema's normalizedDateValue regex is:
#     -?[129]?[0-9][0-9][0-9][019][0-9][01239][0-9]
#
# Year part: optional `-`, optional `1`/`2`/`9`, then exactly 3 digits.
# This means MOM-form years are constrained to:
#   * 3-digit years           100..999  (MOM e.g. "7690101")
#   * 4-digit years           1000..1999, 2000..2999, 9000..9999
#   * Negative variants       -100..-999, -1999..-1000, -2999..-2000, -9999..-9000
# 4-digit years 3000..8999 are NOT representable in MOM and must use
# ISO/dotted/year-only formats. Tests below pin all of this down.


# ---------- Pre-1000 (3-digit) years ---------------------------------


@pytest.mark.parametrize(
    "year_str,year_int",
    [
        ("100", 100),
        ("769", 769),
        ("999", 999),
    ],
)
def test_pre1000_iso_form_with_padding(year_str, year_int):
    result = dates.parse(f"0{year_str}-01-15")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == year_int
    assert result.ymdhms[2] == 15


@pytest.mark.parametrize("year_int", [100, 769, 999])
def test_pre1000_mom_unpadded_form_parses(year_int):
    # MOM uses the schema's unpadded 7-character form.
    mom = f"{year_int}0115"
    result = dates.parse(mom)
    assert isinstance(result, Time)
    assert result.ymdhms[0] == year_int
    assert result.ymdhms[1] == 1
    assert result.ymdhms[2] == 15


@pytest.mark.parametrize("year_int", [100, 769, 999])
def test_pre1000_mom_padded_form_rejected(year_int):
    # Adding a leading zero takes the string out of the schema's regex.
    padded = f"0{year_int}0115"  # 8 chars instead of 7
    with pytest.raises(ValueError):
        dates.parse(padded)


def test_pre1000_dotted_dmy_with_padding():
    result = dates.parse("15.01.0769")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 769


def test_pre1000_dotted_ymd_with_padding():
    result = dates.parse("0769.01.15")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 769


def test_pre1000_bare_year_returns_full_year_range():
    result = dates.parse("0769")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 769 and result[0].ymdhms[1] == 1
    assert result[1].ymdhms[0] == 769 and result[1].ymdhms[1] == 12


def test_pre1000_bare_year_no_padding():
    result = dates.parse("769")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 769


def test_pre1000_round_trip_mom():
    # Parse MOM -> to_mom_date_value should give back the same string.
    mom = "7690115"
    t = dates.parse(mom)
    assert isinstance(t, Time)
    assert dates.to_mom_date_value(t) == mom


def test_pre1000_round_trip_iso_then_mom():
    t = dates.parse("0769-01-15")
    assert isinstance(t, Time)
    assert dates.to_mom_date_value(t) == "7690115"


# ---------- Year boundaries ------------------------------------------


@pytest.mark.parametrize(
    "year",
    [
        100,    # smallest 3-digit
        999,    # largest 3-digit
        1000,   # smallest 4-digit starting with 1
        1999,   # largest "1xxx"
        2000,   # smallest "2xxx"
        2999,   # largest "2xxx"
        9000,   # smallest "9xxx"
        9999,   # largest 4-digit
    ],
)
def test_year_boundaries_round_trip_mom(year):
    expected = f"{year}0115"
    t = dates.parse(expected)
    assert isinstance(t, Time)
    assert t.ymdhms[0] == year
    assert dates.to_mom_date_value(t) == expected


@pytest.mark.parametrize("year", [3000, 4567, 8999])
def test_unrepresentable_mom_years_rejected(year):
    # 3000..8999 are outside the schema regex (leading digit must be 1/2/9
    # for 4-digit years). These cannot be expressed in MOM form.
    mom_attempt = f"{year}0115"
    with pytest.raises(ValueError, match="Invalid MOM date|MOM"):
        dates.parse(mom_attempt)


@pytest.mark.parametrize("year", [3000, 4567, 8999])
def test_unrepresentable_mom_years_iso_works(year):
    # The same years are perfectly fine in ISO form.
    result = dates.parse(f"{year:04d}-01-15")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == year


# ---------- Negative (BCE) years -------------------------------------


@pytest.mark.parametrize("year", [-100, -450, -999, -1000, -1999, -2000])
def test_bce_years_mom_round_trip(year):
    # Negative years that both the MOM regex AND astropy/ERFA accept.
    mom = f"-{abs(year)}0115"
    t = dates.parse(mom)
    assert isinstance(t, Time)
    assert t.ymdhms[0] == year
    assert dates.to_mom_date_value(t) == mom


def test_extreme_bce_year_passes_regex_but_astropy_rejects():
    # Year -9999 is permitted by the MOM regex but ERFA's dtf2d refuses it
    # ("bad year"). Pin the boundary so future contributors don't think
    # this is a parser bug.
    with pytest.raises(Exception):
        dates.parse("-99990115")


def test_bce_year_dotted():
    result = dates.parse("15.01.-450")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == -450


# ---------- MOM "unknown" sentinels in pre-1000 contexts -------------


def test_pre1000_mom_unknown_day():
    # March in year 769, unknown day -> full-month range.
    result = dates.parse("7690399")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 769
    assert result[0].ymdhms[1] == 3
    assert result[0].ymdhms[2] == 1
    assert result[1].ymdhms[2] == 31  # March has 31 days


def test_pre1000_mom_unknown_month():
    result = dates.parse("7699999")
    assert isinstance(result, tuple)
    assert result[0].ymdhms[0] == 769
    assert result[0].ymdhms[1] == 1
    assert result[1].ymdhms[1] == 12
    assert result[1].ymdhms[2] == 31


def test_unknown_day_in_february_non_leap():
    # 1457 is not a leap year — Feb has 28 days.
    result = dates.parse("14570299")
    assert isinstance(result, tuple)
    assert result[1].ymdhms[2] == 28


def test_unknown_day_in_february_leap_year():
    # 1456 is a leap year — Feb has 29 days.
    result = dates.parse("14560299")
    assert isinstance(result, tuple)
    assert result[1].ymdhms[2] == 29


# ---------- Leap-year boundary days ----------------------------------


def test_leap_day_exact():
    result = dates.parse("14560229")
    assert isinstance(result, Time)
    assert result.ymdhms[1] == 2
    assert result.ymdhms[2] == 29


def test_non_leap_feb_29_rejected():
    # Astropy will reject day 29 in a non-leap February at construction.
    with pytest.raises(Exception):
        dates.parse("14570229")


# ---------- Schema regex day-range nuances ---------------------------
#
# The schema day part `[01239][0-9]` allows 00-39 and 90-99 but NOT 40-89.
# This means days 40-89 fail the regex even though they'd never be valid
# calendar days anyway. Verify the regex does its job.


@pytest.mark.parametrize("bad_day", ["40", "55", "67", "89"])
def test_mom_regex_rejects_impossible_day_codes(bad_day):
    with pytest.raises(ValueError, match="Invalid MOM"):
        dates.parse(f"14570{bad_day[0]}{bad_day[1]}".replace(" ", ""))
    # And the canonical form too
    with pytest.raises(ValueError, match="Invalid MOM"):
        dates.parse(f"145703{bad_day}")


# ---------- The "no date" sentinel ------------------------------------


def test_no_date_sentinel_returns_none():
    assert dates.parse("99999999") is None


def test_no_date_sentinel_round_trip_via_charter():
    # Charter stores None and serializes the @value="99999999" sentinel.
    from to_cei import Charter
    c = Charter("1", date_value="99999999")
    assert c.date_value is None


# ---------- Round-trip property: parse(to_mom(t)) == t ---------------


@pytest.mark.parametrize(
    "year,month,day",
    [
        (100, 1, 1),
        (769, 3, 15),
        (999, 12, 31),
        (1000, 6, 15),
        (1456, 2, 29),  # leap day
        (1457, 3, 15),
        (1999, 12, 31),
        (2000, 1, 1),
        (9999, 12, 31),
        (-450, 3, 15),
        (-999, 1, 1),
    ],
)
def test_mom_round_trip_property(year, month, day):
    t = Time({"year": year, "month": month, "day": day}, format="ymdhms", scale="ut1")
    mom = dates.to_mom_date_value(t)
    parsed = dates.parse(mom)
    assert isinstance(parsed, Time)
    assert parsed.ymdhms[0] == year
    assert parsed.ymdhms[1] == month
    assert parsed.ymdhms[2] == day


# --------------------------------------------------------------------#
#         Years under 100: padding required, ambiguity warnings       #
# --------------------------------------------------------------------#
#
# These are documentation-by-test. They pin down the year-12 corner
# cases discussed in the README's "Years under 100" subsection so a
# future change can't silently flip the dispatch order or relax the
# MOM regex without a test failure flagging it.


# ---------- Year 12, December 11 — well-padded inputs all agree -----


@pytest.mark.parametrize(
    "input_str",
    [
        "0012-12-11",   # ISO with 4-char padded year
        "0121211",      # MOM with year padded to 3 chars (7 chars total)
        "11.12.0012",   # German dotted DMY, year padded to 4 chars
        "0012.12.11",   # dotted YMD, year padded to 4 chars
        "11/12/0012",   # slashed DMY, year padded to 4 chars
    ],
)
def test_year_12_padded_forms_all_parse_to_same_date(input_str):
    result = dates.parse(input_str)
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 12
    assert result.ymdhms[1] == 12
    assert result.ymdhms[2] == 11


# ---------- Year 12 in MOM form: padding is mandatory ---------------


def test_year_12_mom_unpadded_rejected():
    # Year 12 must be written as "012" → 7-char MOM string "0121211".
    # The 6-char string "121211" doesn't satisfy the schema regex's
    # 3-char minimum year part.
    with pytest.raises(ValueError):
        dates.parse("121211")


def test_year_12_mom_padded_round_trip():
    t = dates.parse("0121211")
    assert isinstance(t, Time)
    assert dates.to_mom_date_value(t) == "0121211"


# ---------- 2-digit year ambiguity: DMY beats YMD -------------------


def test_two_digit_year_dotted_parses_as_dmy_not_ymd():
    # "12.12.11" is parsed by the German DMY parser first
    # (day=12, month=12, year=11), not as YMD (year=12, month=12, day=11).
    # This is intentional and stable — German archival data is the
    # primary use case and DMY is the convention there.
    result = dates.parse("12.12.11")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 11   # year, not 12
    assert result.ymdhms[1] == 12
    assert result.ymdhms[2] == 12   # day, not 11


def test_two_digit_year_hyphen_parses_as_dmy_not_iso():
    # "12-12-11" is parsed by the rare hyphen-DMY parser
    # (day=12, month=12, year=11), not by ISO. ISO requires a hyphen at
    # string position 4, and a 2-digit year doesn't reach that far.
    result = dates.parse("12-12-11")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 11
    assert result.ymdhms[1] == 12
    assert result.ymdhms[2] == 12


def test_padding_year_to_4_chars_disambiguates_to_ymd():
    # With a fully-padded year on either end the YMD parser wins
    # because the DMY parser's day/month groups can't match 4 digits.
    result = dates.parse("0011.12.12")
    assert isinstance(result, Time)
    assert result.ymdhms[0] == 11   # year (now unambiguous)
    assert result.ymdhms[1] == 12
    assert result.ymdhms[2] == 12
