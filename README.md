# to-cei

to-cei builds [CEI](http://www.cei.lmu.de/) (Charter Encoding Initiative) XML
for imports into [Monasterium.net](https://www.monasterium.net) from plain
Python values. A conversion script reads a source such as a spreadsheet or an
archival database export, creates a `Charter` for each charter and writes them
as a `CharterGroup`, the form Monasterium's import takes.

It requires Python 3.13 or newer.

## Installation

```sh
uv add to-cei
# or
pip install to-cei
```

## Quick start

```python
from to_cei import Charter, CharterGroup, Seal

charter = Charter(
    id_text="1307 II 22",
    abstract="Konrad von Lintz beurkundet einen Vertrag mit Heinrich.",
    issuers="Konrad von Lintz",
    issued_place="Wien",
    date="1307 Februar 22",
    date_value="13070222",
    archive="Stiftsarchiv Schotten",
    seal_description="2 Siegel",
    seals=[Seal(sigillant="Konrad von Lintz", material="Wachs")],
)

group = CharterGroup("Schotten OSB", [charter])
group.to_file("./out")  # writes ./out/schotten_osb.cei.group.xml
```

The docstrings of `Charter`, `Seal`, `CharterGroup` and `to_cei.dates.parse`
describe every argument.

## Creating charters

### Text or element

Every argument takes a plain value for the common case, and to-cei builds the
CEI element from it. Where CEI allows richer content than plain text, for
example persons marked up in an abstract or a note in the dating, the argument
also accepts the complete CEI element. `to_cei.CEI` builds such elements in the
namespace `to_cei.CEI_NS`:

```python
from to_cei import CEI, Charter

Charter(
    id_text="1307 II 22",
    abstract=CEI.abstract(
        CEI.issuer(CEI.persName("Konrad von Lintz")),
        " beurkundet einen Vertrag mit ",
        CEI.persName("Heinrich"),
        ".",
    ),
    index_persons=["Konrad von Lintz", CEI.persName("Heinrich", key="(DE-588)1")],
)
```

The same rules apply to every argument:

- Repeatable arguments take one entry or a sequence. Each entry is text or an
  element, and `seals`, `text_witnesses` and `Seal(legend=...)` also take
  `Seal`, `TextWitness` and `Legend` entries.
- An element must be in the CEI namespace and have the tag the argument writes.
  A wrong element raises `ValueError` when it's assigned.
- to-cei writes a copy of a passed element and never moves or changes the
  caller's element.
- An element replaces everything to-cei would build for it. Arguments that feed
  into the same element must stay empty, and `to_xml()` raises `ValueError`
  otherwise. This applies to `abstract` with `issuers` and `recipient`, to
  `date` with `date_value`, and to `seal_description` with `seals`.
- An empty string counts as missing, except in `id_text`, the name of a
  `CharterGroup` and the fields of `Legend` and `TextWitness`, which must not be
  empty.

### Dates

`date` holds the text of the issue date and `date_value` its value. `date_value`
accepts every form `to_cei.dates.parse` understands. These are ISO dates and MOM
value forms, numeric dates with dots, slashes or hyphens, bare years, `date`,
`datetime` and `MomDate` objects, and `(start, end)` tuples of them. An empty
string and `"99999999"` mean no date.

`parse` reads only forms that don't depend on a language. Expressions in a
natural language, such as "um 1457", "15. Jh." or "20. September 1246", need a
parser in `extra_parsers`, and a project maps its own no-date markers, such as
"sine dato", to `None` before parsing. Natural-language forms differ between
sources, so each project covers the ones its sources use.

```python
from to_cei import dates

dates.parse("15.03.1457")  # MomDate(year=1457, month=3, day=15)
dates.parse("14570399")  # March 1457 as a range
dates.parse(("1457", "1460"))  # 1457-01-01 to 1460-12-31
dates.parse("99999999")  # None
```

An explicit range runs from the first day of its start to the last day of its
end, and a range whose ends are the same day becomes a single date.

#### How to-cei writes dates

to-cei reads the MOM value forms with `99` for an unknown day or month as a
short way to enter a period. It writes every date as calendar days, because a
value with `99` names no day. A single day becomes `cei:date[@value]`, and a
period becomes `cei:dateRange` with its first and last day. Each charter gets
exactly one `cei:date` or one `cei:dateRange`, because Monasterium's views
choose between them by different rules. CEI allows several dates per charter and
values with `99`, and Monasterium's database holds dates in both forms.

Without a `date` text, to-cei writes the value as the text, for example
`1457-03-15` or `1457-01-01 – 1457-12-31`. A charter without a date gets
`cei:date[@value="99999999"]`, the value Monasterium uses for an unknown date,
with the text "Sine dato", although CEI would allow leaving the date out. A date
text without a value gets the same `@value`.

Days are checked against the Julian leap rule, so every year divisible by 4 has
a 29 February, and `"13000299"` ends on 29 February 1300. The `MomDate`
docstring gives the reason. Years count astronomically, so year 0 is 1 BCE, and
years 0, -4 and -8 are leap years.

A `cei:date` or `cei:dateRange` element passed as `date` is written as given, so
these rules cover only what to-cei builds from `date_value`.

### Matching Monasterium's Excel import

Where Monasterium's Excel import gives a field a fixed form in CEI, to-cei
writes the same form, so a charter with the same content looks the same in
Monasterium whichever route it took:

- Issuers and recipient follow the abstract text, the issuers after
  `" Aussteller: "` and separated by `"; "`, the recipient after
  `" Empfänger: "`.
- A space separates the form of tradition of a textual witness from its text.
- `witnesses` writes Monasterium's witness index, `cei:persName[@type="Zeuge"]`
  in `cei:back`.

The spreadsheet's input conventions don't apply. Repeatable values are Python
sequences, and to-cei never splits text, so a "$$" in a value stays in the text.

Witnesses are the one place where to-cei adds to the copy of a passed element. A
passed `cei:persName` gets `@type="Zeuge"` on its copy, and an element with
another `@type` raises `ValueError`. Witnesses within the text are marked up
with `cei:testis` in an `abstract` or `transcription` element.

## Writing files for import

### Ids and file names

`id_text` is the charter's identifier as the source gives it, written as
`cei:body/cei:idno`. It is also the shelf mark in `cei:archIdentifier` unless
`archive_signature` sets one.

`id_norm` defaults to `id_text`, and to-cei cleans it with `mom_id`, which
applies the rules of Monasterium's import. These rules keep a ";" and turn an id
that ends up empty into "0000". The result is the `@id` of `cei:body/cei:idno`
and the charter's file name `<id_norm>.cei.xml`, and the import leaves it
unchanged.

A cleaned id can contain characters that Windows doesn't allow in file names,
such as the `|` that replaces a `/`, so `to_file()` fails there for such a
charter.

`CharterGroup.to_xml()` raises `ValueError` if two charters have the same
`id_norm`, because the import would number them and an Atom entry would
overwrite the other. The group's file name comes from its name, folded to ASCII
and lowercased. Each run of characters other than letters, digits and `_`
becomes `_`, and `_` at either end is dropped. `to_file(filename=...)` sets
another name.

### Output

`to_xml()` returns the CEI as an lxml element. `to_string()` and `to_file()`
write it as it is, without indentation, because whitespace in mixed content is
part of the text.

Where to-cei builds a mixed-content element from several parts, such as a seal,
the seal description or the archive identifier, it puts a space between two
texts that would otherwise run together. It adds none where one of them already
has whitespace at that edge, and it never changes a passed element.

## Validating output

```python
from to_cei import Validator

validator = Validator()
validator.validate_cei(charter.to_xml())  # raises XMLSchemaValidationError if invalid
validator.is_valid_cei(charter.to_xml())  # returns a bool
```

The XSD is fetched from the
[mom-ca repository](https://github.com/icaruseu/mom-ca) on GitHub and cached on
disk as `~/.cache/to-cei/cei.xsd` after the first fetch. The cached copy doesn't
expire. `Validator(refresh=True)` fetches the current schema and replaces it.

## Using the parts on their own

`mom_id(text)` cleans an id as described under
[Ids and file names](#ids-and-file-names). Data that reaches the database
without the import, for example as an Atom entry, needs this form, because
nothing cleans it there. `mom_id` also gives the id of an existing charter from
its shelf mark.

`to_cei.dates` reads source dates without a charter. `parse` returns a
`MomDate`, a `(MomDate, MomDate)` range or `None`, `to_mom_date_value` writes
the MOM value form of a date, and `is_no_date` checks for a no-date value.

## Development

```sh
uv sync            # install the dependencies into .venv
uv run pytest      # run tests
uv run ruff format # format Python, including code blocks in Markdown
uv run ruff check  # lint
uv run pyright     # type-check
```

The tests fetch the current CEI schema once per run, so they need network
access.
