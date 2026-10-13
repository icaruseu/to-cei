import re
from datetime import datetime

import pytest

from to_cei import dates
from to_cei.dates import MomDate


def test_parse_iso_string_returns_single_time():
    result = dates.parse("1457-03-15")
    assert isinstance(result, MomDate)
    assert result.year == 1457
    assert result.month == 3
    assert result.day == 15


def test_parse_mom_exact_returns_single_time():
    result = dates.parse("14570315")
    assert isinstance(result, MomDate)
    assert result.year == 1457


def test_parse_mom_unknown_day_returns_full_month_range():
    result = dates.parse("14570399")
    assert isinstance(result, tuple)
    assert result[0].day == 1
    assert result[1].day == 31  # March has 31 days


def test_parse_mom_unknown_month_returns_full_year_range():
    result = dates.parse("14579999")
    assert isinstance(result, tuple)
    assert result[0].month == 1
    assert result[0].day == 1
    assert result[1].month == 12
    assert result[1].day == 31


def test_parse_iso_tuple_returns_time_pair():
    result = dates.parse(("1457-03-15", "1457-03-20"))
    assert isinstance(result, tuple)
    assert result[0].day == 15
    assert result[1].day == 20


def test_parse_datetime():
    result = dates.parse(datetime(1457, 3, 15))
    assert isinstance(result, MomDate)
    assert result.year == 1457


def test_parse_datetime_tuple():
    result = dates.parse((datetime(1457, 3, 15), datetime(1457, 3, 20)))
    assert isinstance(result, tuple)
    assert result[0].day == 15


def test_parse_mom_date_returned_as_is():
    t = MomDate(1457, 3, 15)
    assert dates.parse(t) is t


def test_parse_iso_typo_raises_value_error():
    with pytest.raises(ValueError, match="Invalid ISO date"):
        dates.parse("1457-13-01")


def test_parse_empty_string_returns_none():
    assert dates.parse("") is None


def test_parse_none_returns_none():
    assert dates.parse(None) is None


def test_parse_mom_no_date_value_returns_none():
    assert dates.parse("99999999") is None


def test_parse_garbage_raises():
    with pytest.raises(ValueError):
        dates.parse("not a date")


def test_parse_negative_year_mom():
    # The MOM regex permits a leading minus.
    result = dates.parse("-4500315")
    assert isinstance(result, MomDate)
    assert result.year == -450


@pytest.mark.parametrize("value", [1457, 14570315.0, ["1457", "1460"]])
def test_parse_rejects_other_types(value):
    with pytest.raises(TypeError, match="expected text, a date or a MomDate"):
        dates.parse(value)


def test_parse_invalid_tuple_length():
    with pytest.raises(ValueError):
        dates.parse(("14570315",))  # pyright: ignore[reportArgumentType]


def test_to_mom_date_value_roundtrip():
    t = dates.parse("14570315")
    assert isinstance(t, MomDate)
    assert dates.to_mom_date_value(t) == "14570315"


def test_dotted_dmy_german_format():
    result = dates.parse("15.03.1457")
    assert isinstance(result, MomDate)
    assert (result.year, result.month, result.day) == (1457, 3, 15)


def test_dotted_ymd_format():
    result = dates.parse("1457.03.15")
    assert isinstance(result, MomDate)
    assert (result.year, result.month, result.day) == (1457, 3, 15)


def test_slash_dmy_format():
    result = dates.parse("15/03/1457")
    assert isinstance(result, MomDate)
    assert result.day == 15


def test_year_only_returns_full_year_range():
    result = dates.parse("1457")
    assert isinstance(result, tuple)
    assert result[0].month == 1 and result[0].day == 1
    assert result[1].month == 12 and result[1].day == 31


@pytest.mark.parametrize(
    "text",
    ["um 1457", "1457 oder 1458", "15. Jh.", "20. September 1246", "sine dato"],
)
def test_natural_language_needs_an_extra_parser(text):
    with pytest.raises(ValueError, match="Cannot parse date"):
        dates.parse(text)


def test_iso_takes_precedence_over_year():
    result = dates.parse("1457-03-15")
    assert isinstance(result, MomDate)
    assert result.day == 15


def test_unparseable_string_lists_every_attempt():
    with pytest.raises(ValueError, match="Tried:") as excinfo:
        dates.parse("nonsense gibberish")
    msg = str(excinfo.value)
    for name in ("iso", "mom", "dotted", "year"):
        assert name in msg


def test_dotted_in_tuple():
    result = dates.parse(("15.03.1457", "20.03.1457"))
    assert isinstance(result, tuple)
    assert result[0].day == 15
    assert result[1].day == 20


@pytest.mark.parametrize("value", ["99999999", "", "   "])
def test_is_no_date_recognises_no_date_values(value):
    assert dates.is_no_date(value)


@pytest.mark.parametrize(
    "not_marker", ["1457", "1457-03-15", "um 1457", "sine dato", "abc"]
)
def test_is_no_date_rejects_real_dates(not_marker):
    assert not dates.is_no_date(not_marker)


def test_is_no_date_non_string_returns_false():
    assert not dates.is_no_date(None)  # pyright: ignore[reportArgumentType]
    assert not dates.is_no_date(1457)  # pyright: ignore[reportArgumentType]


def test_charter_date_value_accepts_no_date_tuple():
    from to_cei import Charter

    c = Charter("1", date_value=("99999999", ""))
    assert c.date_value is None


def test_extra_parser_handles_format_builtins_dont():
    def anno_domini(text: str) -> tuple[MomDate, MomDate]:
        m = re.fullmatch(r"anno domini (\d{3,4})", text, re.IGNORECASE)
        if m is None:
            raise ValueError("not an 'anno domini' year")
        year = int(m.group(1))
        return (MomDate(year, 1, 1), MomDate(year, 12, 31))

    result = dates.parse("anno domini 1457", extra_parsers=[anno_domini])
    assert result == (MomDate(1457, 1, 1), MomDate(1457, 12, 31))


def test_extra_parser_runs_after_builtins():
    # Built-ins handle "1457", so the extra parser must not see it.
    seen = []

    def trap(text: str) -> MomDate:
        seen.append(text)
        raise ValueError("not mine")

    dates.parse("1457", extra_parsers=[trap])
    assert seen == []


def test_extra_parser_for_format_builtins_reject():
    def roman(text: str) -> MomDate:
        if text != "MCDLVII":
            raise ValueError("not roman")
        return MomDate(1457, 1, 1)

    result = dates.parse("MCDLVII", extra_parsers=[roman])
    assert isinstance(result, MomDate)
    assert result.year == 1457


def test_extra_parser_failure_listed_in_error():
    def always_fail(_: str) -> MomDate:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="always_fail: nope"):
        dates.parse("garbage gibberish", extra_parsers=[always_fail])


def test_extra_parsers_accepts_list_or_tuple():
    def passthrough(_: str) -> MomDate:
        return MomDate(2000, 1, 1)

    assert dates.parse("xyz", extra_parsers=[passthrough]) == MomDate(2000, 1, 1)
    assert dates.parse("xyz", extra_parsers=(passthrough,)) == MomDate(2000, 1, 1)


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
    assert isinstance(result, MomDate)
    assert result.year == year_int
    assert result.day == 15


@pytest.mark.parametrize("year_int", [100, 769, 999])
def test_pre1000_mom_unpadded_form_parses(year_int):
    # MOM uses the schema's unpadded 7-character form.
    mom = f"{year_int}0115"
    result = dates.parse(mom)
    assert isinstance(result, MomDate)
    assert result.year == year_int
    assert result.month == 1
    assert result.day == 15


@pytest.mark.parametrize("year_int", [100, 769, 999])
def test_pre1000_mom_padded_form_rejected(year_int):
    # Adding a leading zero takes the string out of the schema's regex.
    padded = f"0{year_int}0115"
    with pytest.raises(ValueError):
        dates.parse(padded)


def test_pre1000_dotted_dmy_with_padding():
    result = dates.parse("15.01.0769")
    assert isinstance(result, MomDate)
    assert result.year == 769


def test_pre1000_dotted_ymd_with_padding():
    result = dates.parse("0769.01.15")
    assert isinstance(result, MomDate)
    assert result.year == 769


def test_pre1000_bare_year_returns_full_year_range():
    result = dates.parse("0769")
    assert isinstance(result, tuple)
    assert result[0].year == 769 and result[0].month == 1
    assert result[1].year == 769 and result[1].month == 12


def test_pre1000_bare_year_no_padding():
    result = dates.parse("769")
    assert isinstance(result, tuple)
    assert result[0].year == 769


def test_pre1000_round_trip_mom():
    mom = "7690115"
    t = dates.parse(mom)
    assert isinstance(t, MomDate)
    assert dates.to_mom_date_value(t) == mom


def test_pre1000_round_trip_iso_then_mom():
    t = dates.parse("0769-01-15")
    assert isinstance(t, MomDate)
    assert dates.to_mom_date_value(t) == "7690115"


@pytest.mark.parametrize(
    "year",
    [
        100,  # smallest 3-digit
        999,  # largest 3-digit
        1000,  # smallest 4-digit starting with 1
        1999,  # largest "1xxx"
        2000,  # smallest "2xxx"
        2999,  # largest "2xxx"
        9000,  # smallest "9xxx"
        9999,  # largest 4-digit
    ],
)
def test_year_boundaries_round_trip_mom(year):
    expected = f"{year}0115"
    t = dates.parse(expected)
    assert isinstance(t, MomDate)
    assert t.year == year
    assert dates.to_mom_date_value(t) == expected


@pytest.mark.parametrize("year", [3000, 4567, 8999])
def test_unrepresentable_mom_years_rejected(year):
    # The schema regex allows a 4-digit year only with a leading 1, 2 or
    # 9, so 3000 to 8999 have no MOM form.
    mom_attempt = f"{year}0115"
    with pytest.raises(ValueError, match="Invalid MOM date|MOM"):
        dates.parse(mom_attempt)


@pytest.mark.parametrize("year", [3000, 4567, 8999])
def test_unrepresentable_mom_years_iso_works(year):
    result = dates.parse(f"{year:04d}-01-15")
    assert isinstance(result, MomDate)
    assert result.year == year


@pytest.mark.parametrize(
    "year", [-100, -450, -999, -1000, -1999, -2000, -2999, -9000, -9999]
)
def test_bce_years_mom_round_trip(year):
    mom = f"-{abs(year)}0115"
    t = dates.parse(mom)
    assert isinstance(t, MomDate)
    assert t.year == year
    assert dates.to_mom_date_value(t) == mom


def test_bce_year_dotted():
    result = dates.parse("15.01.-450")
    assert isinstance(result, MomDate)
    assert result.year == -450


def test_pre1000_mom_unknown_day():
    result = dates.parse("7690399")
    assert isinstance(result, tuple)
    assert result[0].year == 769
    assert result[0].month == 3
    assert result[0].day == 1
    assert result[1].day == 31  # March has 31 days


def test_pre1000_mom_unknown_month():
    result = dates.parse("7699999")
    assert isinstance(result, tuple)
    assert result[0].year == 769
    assert result[0].month == 1
    assert result[1].month == 12
    assert result[1].day == 31


def test_unknown_day_in_february_non_leap():
    # 1457 is not a leap year, so February has 28 days.
    result = dates.parse("14570299")
    assert isinstance(result, tuple)
    assert result[1].day == 28


def test_unknown_day_in_february_leap_year():
    # 1456 is a leap year, so February has 29 days.
    result = dates.parse("14560299")
    assert isinstance(result, tuple)
    assert result[1].day == 29


def test_leap_day_exact():
    result = dates.parse("14560229")
    assert isinstance(result, MomDate)
    assert result.month == 2
    assert result.day == 29


def test_non_leap_feb_29_rejected():
    with pytest.raises(ValueError):
        dates.parse("14570229")


@pytest.mark.parametrize(
    "text", ["13000229", "1300-02-29", "29.02.1300", "1700-02-29", "1900-02-29"]
)
def test_julian_leap_day_accepted_in_gregorian_common_year(text):
    result = dates.parse(text)
    assert isinstance(result, MomDate)
    assert (result.month, result.day) == (2, 29)


def test_unknown_day_in_february_julian_leap_year():
    result = dates.parse("13000299")
    assert result == (MomDate(1300, 2, 1), MomDate(1300, 2, 29))


def test_bce_leap_years_count_astronomically():
    assert MomDate(0, 2, 29).day == 29
    assert MomDate(-4, 2, 29).day == 29
    with pytest.raises(ValueError):
        MomDate(-1, 2, 29)


@pytest.mark.parametrize(
    "year,month,day",
    [(1457, 0, 1), (1457, 13, 1), (1457, 3, 0), (1457, 4, 31), (1457, 2, 29)],
)
def test_mom_date_rejects_impossible_dates(year, month, day):
    with pytest.raises(ValueError, match="out of range"):
        MomDate(year, month, day)


@pytest.mark.parametrize(
    "date,expected",
    [
        (MomDate(1457, 3, 15), "1457-03-15"),
        (MomDate(769, 1, 5), "0769-01-05"),
        (MomDate(0, 1, 1), "0000-01-01"),
        (MomDate(-450, 3, 15), "-0450-03-15"),
    ],
)
def test_mom_date_isoformat(date, expected):
    assert date.isoformat() == expected


@pytest.mark.parametrize(
    "text", ["1457-03-15T12:30", "1457-03-15T12:30:00", "1457-03-15T00:00:00.000"]
)
def test_iso_time_of_day_is_dropped(text):
    assert dates.parse(text) == MomDate(1457, 3, 15)


@pytest.mark.parametrize(
    "text",
    [
        "1457-03-15T25:00:00",
        "1457-03-15T12:60:00",
        "1457-03-15T12",
        "1457-03-15T12:30:00Z",
        "1457-03-15 12:30:00",
    ],
)
def test_iso_invalid_time_of_day_rejected(text):
    with pytest.raises(ValueError, match="Invalid ISO date"):
        dates.parse(text)


@pytest.mark.parametrize("bad_day", ["40", "55", "67", "89"])
def test_mom_regex_rejects_impossible_day_codes(bad_day):
    # The schema day part `[01239][0-9]` excludes 40 to 89.
    with pytest.raises(ValueError, match="Invalid MOM"):
        dates.parse(f"145703{bad_day}")


def test_no_date_sentinel_returns_none():
    assert dates.parse("99999999") is None


def test_no_date_sentinel_round_trip_via_charter():
    from to_cei import Charter

    c = Charter("1", date_value="99999999")
    assert c.date_value is None


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
    t = MomDate(year, month, day)
    mom = dates.to_mom_date_value(t)
    parsed = dates.parse(mom)
    assert isinstance(parsed, MomDate)
    assert parsed.year == year
    assert parsed.month == month
    assert parsed.day == day


@pytest.mark.parametrize(
    "input_str",
    [
        "0012-12-11",  # ISO with 4-char padded year
        "0121211",  # MOM with year padded to 3 chars (7 chars total)
        "11.12.0012",  # dotted DMY, year padded to 4 chars
        "0012.12.11",  # dotted YMD, year padded to 4 chars
        "11/12/0012",  # slashed DMY, year padded to 4 chars
    ],
)
def test_year_12_padded_forms_all_parse_to_same_date(input_str):
    result = dates.parse(input_str)
    assert isinstance(result, MomDate)
    assert result.year == 12
    assert result.month == 12
    assert result.day == 11


def test_year_12_mom_unpadded_rejected():
    # Year 12 is written "012", which gives the 7-character MOM string
    # "0121211".
    # The 6-char string "121211" doesn't satisfy the schema regex's
    # 3-char minimum year part.
    with pytest.raises(ValueError):
        dates.parse("121211")


def test_year_12_mom_padded_round_trip():
    t = dates.parse("0121211")
    assert isinstance(t, MomDate)
    assert dates.to_mom_date_value(t) == "0121211"


def test_two_digit_year_dotted_parses_as_dmy_not_ymd():
    # "12.12.11" is read as DMY, because the YMD pattern needs a year of 3
    # or 4 digits.
    result = dates.parse("12.12.11")
    assert isinstance(result, MomDate)
    assert result.year == 11
    assert result.month == 12
    assert result.day == 12


def test_two_digit_year_hyphen_parses_as_dmy_not_iso():
    # "12-12-11" matches the dotted parser's hyphenated DMY pattern, not
    # ISO. ISO requires a hyphen at string position 4, and "12-12-11" has
    # its first hyphen at position 2.
    result = dates.parse("12-12-11")
    assert isinstance(result, MomDate)
    assert result.year == 11
    assert result.month == 12
    assert result.day == 12


def test_padding_year_to_4_chars_disambiguates_to_ymd():
    # A 4-digit year at the start matches only the YMD pattern, because
    # the DMY day and month groups take at most two digits.
    result = dates.parse("0011.12.12")
    assert isinstance(result, MomDate)
    assert result.year == 11
    assert result.month == 12
    assert result.day == 12


@pytest.mark.parametrize(
    "value,expected",
    [
        (("1457", "1460"), ("14570101", "14601231")),
        (("14570399", "14600599"), ("14570301", "14600531")),
        (("1457", "14600599"), ("14570101", "14600531")),
        (("1457-03-15", datetime(1457, 3, 20)), ("14570315", "14570320")),
        ((MomDate(1300, 2, 1), "13000299"), ("13000201", "13000229")),
    ],
)
def test_explicit_range_runs_from_first_to_last_day(value, expected):
    result = dates.parse(value)
    assert isinstance(result, tuple)
    assert tuple(dates.to_mom_date_value(end) for end in result) == expected


@pytest.mark.parametrize(
    "value",
    [
        ("1457-03-15", "1457-03-15"),
        ("14570315", datetime(1457, 3, 15)),
        (MomDate(1457, 3, 15), MomDate(1457, 3, 15)),
    ],
)
def test_explicit_range_with_equal_ends_is_single_date(value):
    assert dates.parse(value) == MomDate(1457, 3, 15)


def test_explicit_range_of_one_year_stays_range():
    assert dates.parse(("1457", "1457")) == (MomDate(1457, 1, 1), MomDate(1457, 12, 31))


def test_explicit_range_of_no_date_values_is_none():
    assert dates.parse(("99999999", "")) is None


def test_explicit_range_with_one_no_date_marker_raises():
    with pytest.raises(ValueError, match="both ends or neither"):
        dates.parse(("1457", "99999999"))


def test_explicit_range_ending_before_start_raises():
    with pytest.raises(ValueError, match="end before it starts"):
        dates.parse(("1460", "1457"))


def test_extra_parser_range_ending_before_start_raises():
    def reversed_range(text: str) -> tuple[MomDate, MomDate]:
        return (MomDate(1460, 1, 1), MomDate(1457, 1, 1))

    with pytest.raises(ValueError, match="end before it starts"):
        dates.parse("zwischen 1460 und 1457", extra_parsers=[reversed_range])


def test_extra_parser_result_must_be_a_date():
    def wrong_type(text: str) -> MomDate:
        return "1457"  # pyright: ignore[reportReturnType]

    with pytest.raises(ValueError, match="wrong_type returned"):
        dates.parse("anno 1457", extra_parsers=[wrong_type])


def test_extra_parser_range_with_equal_ends_is_single_date():
    def same_day(text: str) -> tuple[MomDate, MomDate]:
        return (MomDate(1457, 3, 15), MomDate(1457, 3, 15))

    assert dates.parse("Iden des März 1457", extra_parsers=[same_day]) == MomDate(
        1457, 3, 15
    )


@pytest.mark.parametrize("year", [3000, 8999, -3000, -8999, 10000, -10000])
def test_to_mom_date_value_raises_for_years_without_value_form(year):
    with pytest.raises(ValueError, match="no MOM value form"):
        dates.to_mom_date_value(MomDate(year, 1, 1))


@pytest.mark.parametrize(
    "parts", [("1457", 3, 15), (1457.0, 3, 15), (True, 1, 1), (1457, None, 15)]
)
def test_mom_date_rejects_parts_that_are_not_integers(parts):
    with pytest.raises(TypeError, match="must be an integer"):
        MomDate(*parts)


def test_mom_date_stores_other_integers_as_int():
    class Year(int):
        pass

    date = MomDate(Year(1457), 3, 15)
    assert type(date.year) is int
    assert date == MomDate(1457, 3, 15)
