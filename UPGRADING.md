# Upgrading

## From 0.4 to 0.5

A conversion script written for 0.4 needs the code changes below. The output
changes matter wherever 0.5 output is compared with or replaces 0.4 output. The
[changelog](CHANGELOG.md) lists every change.

### Code changes

#### Dates

- Replace `astropy.time.Time` with `to_cei.dates.MomDate`. A `Time` argument
  becomes `MomDate(int(t.ymdhms.year), int(t.ymdhms.month), int(t.ymdhms.day))`,
  and `t.ymdhms[0]` becomes `t.year`. `dates.parse()` returns a `MomDate`, a
  `(MomDate, MomDate)` range or `None`, and a function in `extra_parsers`
  returns a `MomDate` or such a range.
- Replace `dates.string_to_time()`, `dates.extract_time()` and
  `dates.mom_date_to_time()` with `dates.parse()`, and the type aliases
  `to_cei.charter.Date` and `to_cei.charter.DateValue` with
  `to_cei.dates.DateInput`.
- `dates.parse()` reads only forms that don't depend on a language. Map the
  project's no-date markers, such as "sine dato", to `None` before parsing, and
  pass a parser for its natural-language forms, such as "um 1457", in
  `extra_parsers`. `dates.NO_DATE_MARKERS` is gone, and `is_no_date()`
  recognizes only empty or whitespace-only strings and `"99999999"`.
- An explicit range `(start, end)` runs to the last day of its end, so
  `("1457", "1460")` covers 1457-01-01 to 1460-12-31.
- `dates.parse()` raises `TypeError` for a value that isn't text, a `date`, a
  `MomDate` or a tuple of them. Code that caught `ValueError` for such values
  catches `TypeError`.
- A `date_value` whose year has no MOM value form (3000 to 8999, -3000 to -8999
  and beyond 9999 in either direction) raises `ValueError` when it is assigned.

#### Arguments

- All arguments of `Charter` after `id_text`, and all arguments of `Seal`, are
  keyword-only. Name each argument, as in `Charter("1", abstract=...)`.
- Arguments check their types when they are assigned and raise `TypeError` with
  the argument's name. An element in a text-only argument such as `archive`, or
  a value that isn't text in `external_link` or `id_text`, raises instead of
  being dropped.
- The attributes of repeatable arguments, such as `issuers` and `seals`, always
  return a list.

#### Seals

- `seals` takes only the individual seals. Pass a general seal description, or a
  complete `cei:sealDesc` element, as `seal_description`.
- `Seal(sigillant=...)` takes text or a complete `cei:sigillant` element. Wrap a
  `cei:persName` or `cei:orgName`, as in `CEI.sigillant(CEI.persName(...))`.
- `Seal(legend=...)` takes `Legend("text", place="recto")` instead of a
  `("recto", "text")` tuple. A tuple is a sequence of legends.
- Free text in a seal, such as how it is attached, goes in
  `Seal(description=...)`.

#### Elements built by hand

Content that 0.4 couldn't write has arguments of its own. Replace hand-built
elements and changes to written files with them:

- `provenance` for `cei:front/cei:provenance`;
- `seal_description` and `Seal(description=...)` for text in `cei:sealDesc` and
  `cei:seal`;
- `archive_signature` and `archive_internal_id` for the shelf mark and its `@n`
  in `cei:archIdentifier`;
- `text_witnesses` for `cei:witListPar`.

`comments`, `footnotes`, `chancellary_remarks`, `abstract_sources`,
`transcription_sources`, the `literature` arguments, `condition`, `dimensions`
and `graphic_urls` also take elements.

`to_xml()` raises `ValueError` where an element and the arguments that feed into
it are both set, as [Text or element](README.md#text-or-element) lists.

#### Validation

Import `CacheFetchError` from `to_cei.validator`. The schema cache is the file
`~/.cache/to-cei/cei.xsd`. Delete the other files in `~/.cache/to-cei/`.

### Output changes

#### Ids

`id_norm`, and with it `@id` and the file name of `Charter.to_file()`, is the
charter id in the form `mom_id` gives it, where 0.4 percent-encoded it. An id
made only of ASCII letters, digits, `_`, `.`, `-` and `~` is the same in both
versions. Any other id differs:

| `id_text`    | 0.4                     | 0.5           |
| ------------ | ----------------------- | ------------- |
| `1.4.I-001`  | `1.4.I-001`             | `1.4.I-001`   |
| `A/1`        | `A/1`                   | `A\|1`        |
| `1307 II 22` | `1307%20II%2022`        | `1307_II_22`  |
| `ä1`         | `%C3%A41`               | `ä1`          |
| `K//1, n° 1` | `K//1%2C%20n%C2%B0%201` | `K\|\|1_n°_1` |

`CharterGroup` raises `ValueError` if two charters have the same `id_norm`.

#### Text and layout

- A charter without a date reads "Sine dato" with the value `99999999`.
- A date text generated from `date_value` reads `1457-03-15` or
  `1457-01-01 – 1457-12-31`. A range whose ends are the same day is a
  `cei:date`.
- Issuers and recipient follow the abstract text in the form that
  [Monasterium conventions](README.md#monasterium-conventions) describes.
- `Seal` writes its parts in the order sigillant, legend, dimensions, material,
  condition. The parts of `cei:seal`, `cei:sealDesc` and `cei:archIdentifier`
  are separated by a space where their texts would otherwise run together.
- A textual witness with a form of tradition has a space between
  `cei:traditioForm` and the text.
- `cei:archIdentifier/cei:idno` has no `@id`. Only `cei:body/cei:idno` has it.
- `to_string()` and `to_file()` write the XML without indentation.
