# to_cei — Monasterium CEI builder

A small Python library for assembling
[CEI](http://www.cei.lmu.de/) (Charter Encoding Initiative) charters and
charter groups as objects, then serialising them to XML files ready for
import into [Monasterium.net](https://www.monasterium.net).

Requires **Python 3.13+**.

## Install

```sh
pip install to_cei
# or
uv add to_cei
```

## Quick start

Build a minimal valid charter and write it to disk:

```python
from to_cei import Charter

charter = Charter(
    id_text="1457_03_15",
    id_norm="urn:example:1457_03_15",
    date_value="14570315",
    abstract="Konrad von Lintz beurkundet einen Vertrag.",
    issuers="Konrad von Lintz",
    issued_place="Wien",
)

charter.to_file("./out")  # writes ./out/1457_03_15.cei.xml
```

`charter.to_xml()` returns an `lxml._Element` if you would rather embed
the result in a larger pipeline.

## Dates

Real archival data routinely mixes complete dates with partial dates
("only the year is known", "sometime in the 15th century") and "no
date" markers. `to_cei.dates.parse` handles all three: a `Time` for
exact dates, a `(Time, Time)` range for partial ones, `None` for
explicit no-date markers.

```python
from to_cei import dates

# Numeric / standard
dates.parse("1457-03-15")               # ISO 8601         -> Time
dates.parse("14570315")                 # MOM exact        -> Time
dates.parse("14570399")                 # MOM unknown day  -> month range
dates.parse("14579999")                 # MOM unknown month-> year range
dates.parse("15.03.1457")               # German DMY       -> Time
dates.parse("1457.03.15")               # YMD dotted       -> Time
dates.parse("15/03/1457")               # slashed DMY      -> Time

# Year-only and German archival hedging
dates.parse("1457")                     # bare year        -> full year
dates.parse("um 1457")                  # ca./circa/etwa   -> full year
dates.parse("1457 oder 1458")           # either-or        -> 2-year span
dates.parse("zwischen 1457 und 1460")   # between          -> 4-year span
dates.parse("15. Jahrhundert")          # century          -> 1401-1500
dates.parse("Anfang des 15. Jahrhunderts")  # century third

# Explicit range
dates.parse(("1457-03-15", "1457-03-20"))
```

### Recognised string formats (in priority order)

| # | Format | Examples |
|---|---|---|
| 1 | **ISO 8601** | `"1457-03-15"` |
| 2 | **MOM numeric** (`YYYYMMDD`) | `"14570315"`, `"14570399"`, `"14579999"` |
| 3 | **Dotted/slashed numeric** | `"15.03.1457"` (German DMY), `"1457.03.15"` (YMD), `"15/03/1457"`, `"15-03-1457"` |
| 4 | **Bare year** | `"1457"` → full-year range |
| 5 | **German fuzzy** | `"um/ca./circa/gegen/etwa 1457"`, `"1457 oder 1458"`, `"zwischen X und Y"`, `"15. Jahrhundert"`, `"15. Jh."`, `"Anfang/Mitte/Ende des 15. Jahrhunderts"` |

If parsing fails, the exception lists every format that was tried with
its rejection reason — so you can see at a glance whether your input
just needs a small reformat or a new parser.

### Plug in your own format

If your data has a dialect the built-ins don't cover, pass a parser via
`extra_parsers=`. It receives a stripped, non-empty, non-no-date string
and must either return a `Time` / `(Time, Time)` or raise `ValueError`
to mean "not my format" — exactly the contract the built-ins follow.
Extra parsers run **after** the built-ins, so they only see strings
nothing else could handle:

```python
def julian_day(text: str) -> Time:
    if not text.startswith("JD"):
        raise ValueError("not a julian-day string")
    return Time(float(text[2:]), format="jd", scale="ut1")

dates.parse("JD2451545.0", extra_parsers=[julian_day])
```

`Charter(date_value=...)` accepts the same shapes (it delegates to
`parse`), so this also works at construction time.

### "No date" markers

Real catalogues use a small zoo of "no date" labels. `parse` recognises
them and returns `None` — they're a meaningful value, not an error:

```python
dates.parse("sine dato")    # Latin    -> None
dates.parse("s.d.")
dates.parse("ohne Datum")   # German   -> None
dates.parse("o.D.")
dates.parse("undatiert")
dates.parse("n.d.")         # English  -> None
dates.parse("undated")
dates.parse("99999999")     # MOM sentinel -> None
dates.parse("")             # empty -> None
```

`Charter(date_value=...)` delegates to `parse`, so any of these strings
produce `date_value=None` (serialized as `@value="99999999"`). Use
`to_cei.dates.is_no_date(text)` for an explicit predicate; the full list
lives in `to_cei.dates.NO_DATE_MARKERS`.

## Multiple issuers

```python
Charter(
    id_text="example",
    issuers=["Konrad von Lintz", "Heinrich der Praitenvelder"],
)
```

## Abstract as XML

When you need structured markup inside the abstract (e.g. nested
`persName` elements), pass an `lxml` element instead of a string. Note
that doing so currently means you must build the issuer markup into the
abstract yourself — `issuers=` and an XML abstract are mutually
exclusive at serialisation time.

```python
from lxml import etree
from to_cei.config import CEI

abstract = CEI.abstract(
    "Konrad von Lintz beurkundet einen Vertrag mit ",
    CEI.persName("Heinrich"),
    ".",
)

Charter(id_text="example", abstract=abstract)
```

## Image URLs (`graphic_urls`)

`graphic_urls` accepts **anything from a full URL down to a bare
filename** — the CEI schema doesn't care, and Monasterium resolves
short forms against a per-fond / per-collection `base_url` configured
on the server. The most common new-user trap is assuming you must
always supply a fully-qualified URL.

```python
# All three are valid CEI:
Charter("1", graphic_urls="https://example.org/charters/1.jpg")  # full URL
Charter("1", graphic_urls="2024/scans/1.jpg")                    # path fragment
Charter("1", graphic_urls="1.jpg")                               # bare filename
```

When to use which:

- **Full URL** — required if the image lives somewhere outside the
  fond/collection's configured `base_url`, or if you're producing CEI
  for use outside Monasterium.
- **Path fragment / bare filename** — preferred when all images for a
  fond live under a common base. Monasterium joins them with the
  fond's `base_url` at display time, so you avoid hard-coding the host
  in every charter and the fond can be moved later without rewriting
  the data. Coordinate the base path with whoever administers the
  fond on Monasterium.

Pass a list for multiple images:

```python
Charter("1", graphic_urls=["1_recto.jpg", "1_verso.jpg"])
```

## Charter groups

```python
from to_cei import Charter, CharterGroup

group = CharterGroup(
    name="Schotten OSB",
    charters=[Charter(id_text="a"), Charter(id_text="b")],
)
group.to_file("./out")
```

## Validation

```python
from to_cei import Charter, Validator

v = Validator()                     # downloads + caches the CEI XSD once
v.validate_cei(charter.to_xml())    # raises XMLSchemaValidationError on failure
v.is_valid_cei(charter.to_xml())    # bool variant
```

The XSD is cached on disk under `~/.cache/to-cei/` after the first fetch.

## Field reference

See [`docs/fields.md`](docs/fields.md) for the complete table of every
`Charter`, `Seal`, and `CharterGroup` keyword argument with the CEI
element each one produces.

## Develop

```sh
uv sync           # create the venv with deps
uv run pytest     # run tests
just test         # same, via the justfile
```
