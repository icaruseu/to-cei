# Charter field reference

Every keyword argument accepted by `Charter(...)`. All fields are optional
unless noted; empty strings are treated as missing.

| kwarg | type | what it produces | notes |
|---|---|---|---|
| `id_text` | `str` (**required**) | becomes `cei:idno` text and the basis of the file slug | non-empty; raises `ValueError` if missing |
| `id_norm` | `str` | percent-encoded `cei:idno/@id` | falls back to a normalized `id_text` |
| `id_old` | `str` | `cei:altIdentifier[@type="old"]` | |
| `abstract` | `str` \| `etree._Element` | `cei:abstract` | XML element here means `issuers` must be `None` (checked at `to_xml`) |
| `abstract_sources` | `str` \| `list[str]` | `cei:bibl` entries inside `cei:sourceDescRegest` | |
| `archive` | `str` | `cei:arch` | |
| `archive_location` | `str` | settlement of the holding archive | |
| `chancellary_remarks` | `str` \| `list[str]` | `cei:nota` | |
| `comments` | `str` \| `list[str]` | `cei:p` inside `cei:diplomaticAnalysis` | |
| `condition` | `str` | `cei:condition` | |
| `date` | `str` \| `etree._Element` | `cei:date` or `cei:dateRange` | if XML, `date_value` must remain unset |
| `date_quote` | `str` \| `etree._Element` | `cei:quoteOriginaldatierung` | |
| `date_value` | ISO string, MOM string, `datetime`, `astropy.Time`, or 2-tuple | `cei:date[@value]` / `cei:dateRange[@from][@to]` | use `to_cei.dates.parse` for advance parsing; `"99999999"` → "no date" |
| `dimensions` | `str` | `cei:dimensions` | |
| `external_link` | `str` | `cei:ref/@target` | must be `http(s)://host.tld...` (validated) |
| `fond` | `str` | `cei:archFond` | |
| `footnotes` | `str` \| `list[str]` | `cei:nota` (footnote variant) | |
| `graphic_urls` | `str` \| `list[str]` | `cei:graphic/@url` per `cei:figure` | accepts anything from full URL to bare filename — see below |
| `index` | `list[str \| etree._Element]` | `cei:index` | strings auto-wrapped |
| `index_geo_features` | `list[str \| etree._Element]` | `cei:geogName` | |
| `index_organizations` | `list[str \| etree._Element]` | `cei:orgName` | |
| `index_persons` | `list[str \| etree._Element]` | `cei:persName` | |
| `index_places` | `list[str \| etree._Element]` | `cei:placeName` | |
| `issued_place` | `str` \| `etree._Element` | `cei:placeName` inside `cei:issued` | |
| `issuer` | `str` \| `etree._Element` | — | **deprecated**, use `issuers` |
| `issuers` | `str` \| `etree._Element` \| `list[str]` \| `list[etree._Element]` | `cei:issuer` (one or more) | mutually exclusive with an XML `abstract` |
| `language` | `str` | `cei:lang_MOM` | |
| `literature` | `str` \| `list[str]` | `cei:bibl` inside `cei:listBibl` | |
| `literature_abstracts` | `str` \| `list[str]` | `cei:listBibl` (regest variant) | |
| `literature_depictions` | `str` \| `list[str]` | `cei:listBibl` (faksimile variant) | |
| `literature_editions` | `str` \| `list[str]` | `cei:listBibl` (edition variant) | |
| `literature_secondary` | `str` \| `list[str]` | `cei:listBibl` (Erw variant) | |
| `material` | `str` | `cei:material` | |
| `notarial_authentication` | `str` \| `etree._Element` | `cei:notariusDesc` | |
| `recipient` | `str` \| `etree._Element` | `cei:recipient` inside the abstract | |
| `seals` | `str` \| `Seal` \| `list[str]` \| `list[Seal]` \| `etree._Element` | `cei:sealDesc` | pass a `cei:sealDesc` element to bypass the builder |
| `tradition` | `str` | `cei:traditioForm` | original / copy / etc. |
| `transcription` | `str` \| `etree._Element` | `cei:tenor` | |
| `transcription_sources` | `str` \| `list[str]` | `cei:bibl` inside `cei:sourceDescVolltext` | |
| `witnesses` | `list[str \| etree._Element]` | `cei:persName` inside `cei:witListPar` | XML elements get `@type="Zeuge"` automatically |

## Date input shapes

`to_cei.dates.parse` (and therefore `Charter(date_value=...)`) tries
every built-in format in order and returns the first successful parse.
There is no "pick a format" knob — heterogeneous data is the norm.

| group | shape | example | result |
|---|---|---|---|
| ISO 8601 | string | `"1457-03-15"` | exact `Time` |
| MOM exact | string | `"14570315"` | exact `Time` |
| MOM unknown day | string | `"14570399"` | full-month range |
| MOM unknown month | string | `"14579999"` | full-year range |
| Dotted DMY | string | `"15.03.1457"` | exact `Time` |
| Dotted YMD | string | `"1457.03.15"` | exact `Time` |
| Slashed/hyphen DMY | string | `"15/03/1457"`, `"15-03-1457"` | exact `Time` |
| Bare year | string | `"1457"` | full-year range |
| German "around" | string | `"um 1457"`, `"ca. 1457"`, `"circa 1457"`, `"gegen 1457"`, `"etwa 1457"` | full-year range |
| German "either-or" | string | `"1457 oder 1458"` | spans `1457-01-01` … `1458-12-31` |
| German "between" | string | `"zwischen 1457 und 1460"` | spans `1457-01-01` … `1460-12-31` |
| German century | string | `"15. Jahrhundert"`, `"15. Jh."` | `1401-01-01` … `1500-12-31` |
| German century third | string | `"Anfang/Mitte/Ende des 15. Jahrhunderts"` | first/middle/last third of the century |
| datetime | `datetime.datetime` | `datetime(1457, 3, 15)` | `Time` |
| astropy | `astropy.time.Time` | passed through | `Time` |
| explicit range | 2-tuple of any of the above | `("1457-03-15", "1457-03-20")` | `(Time, Time)` range |
| no-date marker | string | `"sine dato"`, `"o.D."`, `"99999999"`, `""` | `None` |

To handle a dialect the built-ins don't cover, pass a parser callable
via `parse(text, extra_parsers=[my_parser])`. Extra parsers run after
all built-ins; the callable must return a `Time` / `(Time, Time)` or
raise `ValueError` for "not my format".

### "No date" markers

Both `dates.parse` and `Charter(date_value=...)` map archival "no date"
labels to `None`, which serializes as `@value="99999999"`. They're a
defined value, not an error. Recognised markers (case- and
whitespace-insensitive):

| language | accepted strings |
|---|---|
| Latin | `sine dato`, `sine die`, `s.d.`, `s. d.`, `sd` |
| German | `ohne Datum`, `o.D.`, `o. d.`, `od`, `kein Datum`, `undatiert` |
| English | `no date`, `n.d.`, `n. d.`, `nd`, `undated` |
| MOM | `99999999`, empty string |

Use `to_cei.dates.is_no_date(text)` to check the same set explicitly.
The full list lives in `to_cei.dates.NO_DATE_MARKERS`.

## `graphic_urls` resolution

The CEI schema places no restriction on `cei:graphic/@url` — it accepts
anything from a fully-qualified URL down to a bare filename. Which form
you should use depends on where the file lives:

- **Full URL** (`"https://example.org/charters/1.jpg"`) is required if
  the file is outside the fond's image base, or if you are producing
  CEI for consumption outside Monasterium.
- **Path fragment** (`"2024/scans/1.jpg"`) or **bare filename**
  (`"1.jpg"`) is preferred when all images for the fond live under a
  common location. Monasterium fonds and collections can configure a
  `base_url` on the server; at display time it is joined with whatever
  is in `@url`, so short forms keep the host out of the data and let
  the fond be relocated later without rewriting every charter.

This means a `graphic_urls` value the library happily accepts can still
be wrong from a Monasterium perspective if the fond's `base_url` isn't
set up to make it resolve. Coordinate with the fond administrator.

## Seal fields

`Seal(condition=, dimensions=, legend=, material=, sigillant=)` —
`legend` accepts a single string or a list of `(place, text)` tuples;
`sigillant` accepts a string or a `cei:persName` / `cei:orgName` element.

## CharterGroup fields

`CharterGroup(name, charters=None)` — `name` is required; the on-disk
filename is derived by ASCII-folding the name (override with
`group.to_file(folder, filename="custom_stem")`).
