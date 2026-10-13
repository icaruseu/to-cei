# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1]

### Fixed

- The docs said that data reaching Monasterium without the import, such as an
  Atom entry, needs the id in the form `mom_id()` gives it. That holds for
  `@id`. The Atom id holds that id percent-encoded.

## [0.5.0]

[UPGRADING.md](UPGRADING.md) describes the changes a conversion script for 0.4
needs.

### Added

- `Validator(refresh=True)` fetches the current CEI schema and replaces the
  cached copy.
- `to_cei` exports `CEI`, the builder for CEI elements, and `CEI_NS`.
- Element arguments for content that CEI allows to be richer than text:
  `comments` (`cei:p`), `footnotes` (`cei:note`), `chancellary_remarks`
  (`cei:nota`), `abstract_sources`, `transcription_sources` and the
  `literature*` arguments (`cei:bibl`), `condition` (`cei:condition`),
  `dimensions` (`cei:dimensions`) and `graphic_urls` (`cei:figure`).
- `Charter(provenance=...)` writes `cei:front/cei:provenance`, as text or a
  `cei:provenance` element.
- `Charter(archive_signature=...)` sets the shelf mark in
  `cei:archIdentifier/cei:idno`, and `Charter(archive_internal_id=...)` its
  `@n`.
- `Charter(seal_description=...)` sets the text of `cei:sealDesc`, or takes a
  complete `cei:sealDesc` element.
- `Seal(description=...)` writes free text at the start of `cei:seal`.
- `Seal(legend=...)` accepts `cei:legend` elements and mixes them with texts and
  `Legend` entries.
- `Charter(text_witnesses=...)` writes the textual witnesses as `cei:witness`
  entries in `cei:witListPar`, as texts, `TextWitness` entries or `cei:witness`
  elements.
- `Legend(text, place=None)` and `TextWitness(text, tradition=None)` describe a
  seal legend with its place and a textual witness with its form of tradition.
- `dates.parse()` and `Charter(date_value=...)` accept `datetime.date`.
- `to_cei.mom_id()` returns a charter id in the form Monasterium's import gives
  it.

### Changed

- Dependency updates.
- BREAKING: Dates are `to_cei.dates.MomDate` (year, month, day) instead of
  `astropy.time.Time`. `dates.parse()` returns `MomDate` or
  `(MomDate, MomDate)`, `parse()` and `Charter(date_value=...)` accept
  `MomDate`, and `extra_parsers` return `MomDate`.
- Generated date text reads `1457-03-15` or `1457-01-01 – 1457-12-31` instead of
  `+01457-03-15` or `+01457-01-01 - +01457-12-31`, and `MomDate.isoformat()`
  returns the same form.
- BREAKING: `Charter(seals=...)` takes only the individual seals. A text entry
  becomes a `cei:seal` with that text, also as a single string.
- BREAKING: `Seal(sigillant=...)` takes text or a complete `cei:sigillant`
  element instead of a `cei:persName` or `cei:orgName`.
- BREAKING: Repeatable arguments, `issuers`, `seals` and `Seal(legend=...)`
  among them, take one entry or a sequence with texts and elements mixed, and
  their attributes always return a list. `to_xml()` checks entries added to such
  a list in place, like an assignment does.
- `CharterGroup` takes one `Charter` or a sequence, and its `name` and
  `charters` raise `TypeError` with the argument's name for a wrong type.
- A passed element is written as a copy and never moved or changed. A
  `cei:persName` in `witnesses` gets `@type="Zeuge"` on its copy, and one with
  another `@type` raises `ValueError`.
- An XML element in `date` together with a `date_value` raises in `to_xml()`
  instead of when `date_value` is set, like `abstract` with `issuers` or
  `recipient`.
- `to_string()` and `to_file()` write the XML as `to_xml()` builds it, without
  indentation. Before, they pretty-printed it and added whitespace inside
  content elements that hold only child elements.
- The parts of `cei:seal`, `cei:sealDesc` and `cei:archIdentifier` are separated
  by a space where their texts would otherwise run together.
- BREAKING: An explicit `(start, end)` range in `dates.parse()` runs to the last
  day of its end, so `("1457", "1460")` ends on 1460-12-31 instead of
  1460-01-01. It takes mixed forms such as a string and a `datetime`, and it
  raises `ValueError` if it ends before it starts or has only one no-date end.
- The CEI schema is cached as the plain file `~/.cache/to-cei/cei.xsd`, and
  importing `to_cei` no longer creates the cache directory.
- BREAKING: `CacheFetchError` moved from `to_cei.filecache` to
  `to_cei.validator`.
- The license is `LGPL-3.0-or-later` instead of `GPL-3.0`.
- BREAKING: `id_norm`, and with it `@id` and the file name of
  `Charter.to_file()`, follows Monasterium's import rules (`mom_id()`) instead
  of percent-encoding, also for an `id_norm` passed explicitly. "1307 II 22"
  becomes `1307_II_22` instead of `1307%20II%2022`, and "K//1, n° 1" becomes
  `K||1_n°_1`. A percent-encoded id lost its `%` signs in Monasterium's import,
  so "1307 II 22" became `130720II2022` there, and a `/` made
  `Charter.to_file()` write into a subfolder.
- Issuers and recipient follow the abstract text as Monasterium's Excel import
  writes them, the issuers after " Aussteller: " and separated by "; ", the
  recipient after " Empfänger: ".
- BREAKING: `CharterGroup.to_xml()`, `to_string()` and `to_file()` raise
  `ValueError` if several charters have the same `id_norm`.
- BREAKING: All arguments of `Charter` after `id_text`, and all arguments of
  `Seal`, are keyword-only.
- BREAKING: `Seal(legend=...)` takes `Legend("text", place="recto")` instead of
  a `("recto", "text")` tuple. A tuple is now a sequence of legends.
- BREAKING: Arguments check their types on assignment and raise `TypeError` with
  the argument's name. An element in a text-only argument such as `archive`, a
  non-text `external_link` and a non-text `id_text` used to be dropped or
  emptied silently.
- BREAKING: `dates.parse()` raises `TypeError` instead of `ValueError` for a
  value that isn't text, a `date`, a `MomDate` or a tuple of them.
- BREAKING: `Charter(date_value=...)` raises `ValueError` for a year that has no
  MOM value form (3000 to 8999, -3000 to -8999, and beyond 9999 in either
  direction), and `dates.to_mom_date_value()` raises for such a date. Before,
  the value was written and failed schema validation.
- A parser in `extra_parsers` must return a `MomDate` or a range that doesn't
  end before it starts, and `parse()` raises `ValueError` otherwise. A range
  with equal ends becomes a single date.
- A charter without a date reads "Sine dato" instead of "No date".
- `Seal` writes its parts in the order the CEI schema declares them: sigillant,
  legend, dimensions, material and condition. Before, they were in alphabetical
  order, with the sigillant last.
- A `TextWitness` with a form of tradition writes a space between
  `cei:traditioForm` and the text, so it reads like Monasterium's Excel import.
- Development uses the type stubs of `types-lxml` instead of `lxml-stubs`, so
  pyright also checks the code that builds elements with `CEI`.

### Removed

- BREAKING: The `astropy` dependency and `astropy.time.Time` input.
- BREAKING: `dates.string_to_time()`, `dates.extract_time()` and
  `dates.mom_date_to_time()`. `dates.parse()` covers all three.
- BREAKING: The type aliases `to_cei.charter.Date` and
  `to_cei.charter.DateValue`. `to_cei.dates.DateInput` replaces them.
- `Seal.to_string()` and `Seal.to_file()`. Both always raised `TypeError`.
  `etree.tostring(seal.to_xml())` serializes a seal.
- BREAKING: The `to_cei.filecache` module with `FileCache`.
- `to_cei.config.XSI_NS`, which nothing used.
- `docs/fields.md`. The docstrings document every argument.
- BREAKING: The German expressions in `dates.parse()` ("um 1457", "1457 oder
  1458", "zwischen X und Y", "15. Jahrhundert", "Anfang des 15. Jahrhunderts"
  and their variants) and `dates.NO_DATE_MARKERS`. `parse()` reads only forms
  that don't depend on a language, and `is_no_date()` recognizes only empty or
  whitespace-only strings and `"99999999"`.

### Fixed

- 29 February in Julian leap years such as 1300 was rejected.
- Years from -9000 to -9999 were rejected although the CEI schema allows them.
- Setting `date` to an XML element after `date_value` silently dropped the
  value.
- An empty `Seal()` next to a `cei:sealDesc` element raised, although it writes
  nothing.
- An interrupted download could leave a cut-off `cei.xsd` in the cache that was
  never fetched again.
- An explicit range with equal ends was written as a `cei:dateRange` instead of
  a `cei:date`.
- A second `to_xml()` call removed passed elements from the result of the first
  call.
- `issuers` and `recipient` were dropped without an `abstract` text.
- The charter identifier appeared with the same `@id` in two `cei:idno`
  elements.
- Without an abstract text, the abstract started with a space before
  "Aussteller:" or "Empfänger:".
- `to_file()` wrote into the current directory for a folder given as a path type
  other than `str` or `Path`, and failed for an empty string.
- A schema cache that couldn't be read or written stopped `Validator()`,
  although the schema had been fetched.
- The package metadata named both GPL-3.0 and LGPL-3.0, and the deprecated
  license table would have stopped builds from 2027-02-18.

## [0.4.4]

### Changed

- `Validator()` fetches the XSD from the mom-ca repository.

## [0.4.3]

Dependency refresh. No code or behaviour changes.

### Changed

- Upgraded locked dependencies to current releases, notably `urllib3` 2.6.3 →
  2.7.0 (security fix) and `cryptography` 46.0.7 → 48.0.0. Also bumped
  `astropy-iers-data`, `build` (1.4.3 → 1.5.0), `certifi` (2026.2.25 →
  2026.4.22), `idna` (3.12 → 3.14), `markdown-it-py` (4.0.0 → 4.2.0), `nh3`
  (0.3.4 → 0.3.5), `packaging` (26.1 → 26.2), and `requests` (2.33.1 → 2.34.0).
  Full test suite (296 tests) passes against the new versions.

## [0.4.2]

Dependency refresh. No code or behaviour changes.

### Changed

- Upgraded locked dependencies to current releases, notably `lxml` 6.0.2 → 6.1.0
  (picks up the XPath use-after-free fix and subsequent follow-ups). Also bumped
  `astropy-iers-data`, `build` (1.4.2 → 1.4.3), `idna` (3.11 → 3.12),
  `more-itertools` (11.0.1 → 11.0.2), `packaging` (26.0 → 26.1), and `rich`
  (14.3.3 → 15.0.0). Full test suite (296 tests) passes against the new
  versions.

## [0.4.1]

Documentation and test-coverage release. No code or behaviour changes to the
runtime API.

### Added

- README "Dates" section rewritten with a "many input forms, one output"
  equivalence example (year 1457 in five formats producing identical `Time`s), a
  worked pre-1000 (3-digit year) example showing which input shapes accept
  padded years and which don't, a "what gets returned" reference table mapping
  each input shape to `Time` / `(Time, Time)` / `None`, and an explicit
  reframing of MOM as "the CEI schema's `@value` attribute format, accepted on
  input for round-tripping" rather than just one input format among many.
- Source comment on `to_cei.dates.MOM_DATE_REGEX` noting that it is copied
  verbatim from the CEI schema's `normalizedDateValue` simple type and must not
  be relaxed, plus the year-padding behaviour (3-digit years are unpadded — year
  769 is `"7690101"`, not `"07690101"`).
- 70 new schema-edge tests in `test/test_dates.py`, taking the total from the
  0.4.0 baseline of **226 to 296**: pre-1000 (3-digit) years across every input
  format, the year-under-100 padding requirements and 2-digit-year DMY/YMD
  ambiguity (documentation-by-test for the README's "Years under 100"
  subsection), the un-representable MOM 3000–8999 range, BCE/negative years,
  year boundaries (100, 999, 1000, 1999, 2000, 2999, 9000, 9999), leap-year
  February-29 handling, the schema-regex day-range nuances (40–89 forbidden),
  the no-date sentinel, the astropy/ERFA `-9999` lower bound, and a parametrized
  round-trip property test asserting `parse(to_mom_date_value(t)) == t` over a
  representative range of years.
- Three new `justfile` recipes — `build` (clean + sdist + wheel +
  `twine check`), `publish-test` (TestPyPI), and `publish` (PyPI). Both publish
  recipes depend on `build`, so a fresh clean build runs automatically before
  any upload.

## [0.4.0]

A correctness, ergonomics, and structural-cleanup release. Requires **Python
3.13+**. The public API surface is largely preserved; behaviour changes are bug
fixes, one intentional relaxation of when constraint errors are raised, and a
widening of `Charter(date_value=...)` to accept archival "no date" markers — see
_Changed_.

> BREAKING: the long-deprecated `Charter(issuer=...)` (singular) kwarg has been
> removed. Migration is one character: `issuer=x` → `issuers=x`, same accepted
> shapes. See _Removed_.

### Added

- New public `to_cei.dates` module with `parse(value)` — a permissive date
  parser that handles the messy strings real archival data throws at you. It
  tries every built-in format in order and returns the first match;
  heterogeneous charter groups (where one charter has `"1457-03-15"` and the
  next has `"um 1457"`) parse without any per-input configuration. Built-in
  formats:
  - **ISO 8601** — `"1457-03-15"`.
  - **MOM numeric** — `"14570315"`, `"14570399"` (unknown day, full-month
    range), `"14579999"` (unknown month, full-year range).
  - **Dotted/slashed numeric** — German DMY and YMD with `.` / `/` / `-`
    separators (`"15.03.1457"`, `"1457.03.15"`, `"15/03/1457"`).
  - **Bare year** — `"1457"` → full-year range.
  - **German archival fuzzy** — `"um 1457"`, `"ca./circa/etwa/gegen 1457"`,
    `"1457 oder 1458"`, `"zwischen 1457 und 1460"`, `"15. Jahrhundert"` /
    `"15. Jh."`, `"Anfang/Mitte/Ende des 15. Jahrhunderts"`.
- `parse(text, extra_parsers=[...])` lets projects plug in custom date dialects
  without forking. Extra parsers follow the same protocol as the built-ins
  (`(str) -> Time | (Time, Time)`, raise `ValueError` for "not my format") and
  run after all built-ins. The protocol is exposed as
  `to_cei.dates.ConventionParser`.
- `parse` returns `Time | tuple[Time, Time] | None`. It raises `ValueError` on
  input no built-in or extra parser recognises, and returns `None` _only_ for
  explicit no-date markers (`sine dato`, `s.d.`, `o.D.`, `n.d.`, `99999999`,
  empty string, …). On `ValueError` the exception message lists every parser
  that was tried with its rejection reason, so format clashes are easy to
  diagnose.
- New `to_cei.dates.is_no_date(text)` predicate and `NO_DATE_MARKERS` frozenset.
  Recognises archival "no date" labels in Latin (`sine dato`, `s.d.`), German
  (`ohne Datum`, `o.D.`, `undatiert`), and English (`no date`, `n.d.`,
  `undated`), plus the MOM `"99999999"` sentinel, `None`, and empty strings.
- `to_cei/__init__.py` re-exports `Charter`, `CharterGroup`, `Seal`,
  `Validator`, and `dates`, so `from to_cei import Charter` works.
- `Validator.is_valid_cei(element) -> bool` as a non-raising companion to
  `validate_cei`.
- `CharterGroup.to_file(filename=...)` parameter for explicit filename override;
  the auto-generated slug is now Unicode-aware (NFKD fold + non-word → `_`).
- `docs/fields.md` — full reference table of every `Charter`, `Seal`, and
  `CharterGroup` keyword argument and the CEI element each produces.
- `.github/workflows/test.yml` — CI running `uv sync && uv run pytest` on Python
  3.14.
- New tests: 15 for `to_cei.dates` (including the historical
  ISO-typo-silently-falls-through-to-MOM bug), instance-aliasing regression
  tests for mutable defaults, both-orders tests for the `abstract`/`issuers` and
  `abstract`/`recipient` constraints, URL validation cases, and `CharterGroup`
  slug edge cases (umlauts, punctuation, explicit override). Test count: **152 →
  226**.

### Changed

- **`Charter(date_value=...)` now accepts archival "no date" markers.**
  Previously only the empty string and the MOM `"99999999"` sentinel mapped to
  `None`; any other unrecognised string raised `ValueError`. Now the full
  `NO_DATE_MARKERS` set (Latin / German / English "no date" labels — see
  _Added_) also maps to `None`, and `Charter` itself delegates fully to
  `dates.parse`, eliminating the duplicated detection that lived in the setter.
  **Strict callers that relied on `Charter(date_value="sine dato")` raising will
  now silently store `None`.** This is intentional — `sine dato` is a defined
  catalogue value, not an error — but worth flagging when upgrading existing
  data pipelines.
- **`Validator` now actually raises on invalid CEI.** Previously `validate_cei`
  silently passed for both valid and invalid input, masking validation failures
  entirely. It now propagates `xmlschema.XMLSchemaValidationError` (or subclass)
  on failure. The `XMLSchema11` instance is also built once per `Validator` and
  cached.
- **`abstract`/`issuers` and `abstract`/`recipient` mutual exclusion is now
  checked at serialization time** (in `_create_cei_abstract`) rather than in the
  setters. The order in which you assign these fields no longer matters — the
  constraint only fires when you call `to_xml()`. This fixes the previous
  bidirectional setter coupling where assignment order could cause confusing
  `ValueError`s.
- `to_cei.dates.string_to_time` (and therefore `Charter(date_value=...)`) now
  catches `ValueError` specifically when attempting ISO parsing instead of
  swallowing all exceptions. Typos like `"1457-13-01"` now raise a useful error
  instead of silently falling through to MOM parsing.
- `external_link` validation rewritten using `urllib.parse.urlparse` instead of
  the overly-permissive `^https?://.{1,}\..{1,}$` regex. URLs without a TLD
  (e.g. `http://localhost`) and non-`http(s)` schemes are now rejected.
- `CharterGroup.to_file` filename slug is now Unicode-aware: umlauts and other
  diacritics are folded to ASCII via `unicodedata.normalize`, and any non-word
  character is replaced with `_` (previously only spaces were replaced).
- `Charter`'s ~36 simple fields are now declared via a single `CharterField`
  descriptor (`to_cei/_fields.py`) instead of repeating the
  property/setter/private-storage triple by hand. **`charter.py`: 1142 → 756
  lines (−34%)**. The public API is unchanged.
- `to_cei/filecache.py` rewritten:
  - Refuses to cache responses that don't look like XML (the historical bug — an
    HTML 404 page got cached as if it were the CEI XSD, and `Validator` then
    silently used it).
  - Checks `response.ok` and `Content-Type` before caching, raising
    `CacheFetchError` with a clear message on failure.
  - Existing poisoned cache entries self-heal: any cached body that fails the
    XML sniff is treated as a miss and re-fetched.
  - Uses a module-level `requests.Session` for connection reuse.
  - Implements proper context-manager protocol and registers
    `atexit.register(self.close)` so the shelve actually flushes.
- Project moved from `setup.py` + `requirements.txt` to `pyproject.toml`.
- `requires-python` set to `>=3.13`. The library uses no 3.14-specific syntax or
  stdlib features; CI tests both 3.13 and 3.14.
- Full PEP-585 / PEP-604 sweep across the package (`List` → `list`,
  `Optional[X]` → `X | None`, etc.).
- README rewritten with install instructions, a quick-start example, and one
  example each for `dates.parse`, multiple issuers, abstract-as-XML, charter
  groups, and validation.

### Fixed

- **CEI schema validation was silently broken.** The `monasterium.net` schema
  URL had been returning HTTP 404 for an unknown period; the bad HTML response
  got cached as the XSD; the `Validator` then either silently passed everything
  (because it didn't propagate exceptions) or raised cryptic
  `XMLResourceParseError`s once `xmlschema` got stricter. Combination of the
  validator-raises and filecache-sniffs fixes above resolves this; the existing
  bad cache entries self-heal.
- Mutable default arguments at class level (`_witnesses: list[...] = []` and
  friends) — eliminated structurally by the descriptor refactor. Two `Charter`
  instances can no longer share list state through the class-level default.
- `Charter.issuers` setter ignored `None`, so once set the field could not be
  cleared via `charter.issuers = None`.
- `Charter.seals` setter had the same `None`-doesn't-reset bug.
- `Seal.legend` default changed from `[]` to `None`; matches the Optional type
  annotation.

### Removed

- BREAKING: `Charter(issuer=...)` (singular, deprecated since the introduction
  of `issuers` plural). Removing a previously-deprecated public kwarg is a
  public-API removal — strictly a major bump under SemVer; this `0.x` release
  exercises the looser `0.x` allowance to ship it in a minor. Migration is one
  character: `issuer=x` → `issuers=x`, same accepted shapes. The deprecation
  warning that fired on every use is gone, and the test suite now runs
  warning-free.
- `setup.py` and `requirements.txt` (replaced by `pyproject.toml`).
- The unused `SIMPLE_URL_REGEX` constant from `to_cei.charter`.
- The single-entry `Schema` enum from `to_cei.validator`.
