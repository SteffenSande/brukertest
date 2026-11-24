# Specly Repo — Agent Guide

This repo is an export of a Specly project (database schema, diagrams,
data products). This project's tables are Open Data Contract Standard
(ODCS v3.2.0) data contracts. You can edit any file; your changes flow
back to Specly when you push them to Git.

## Specly and Git
- This repo and the Specly project are the same model, kept in sync both
  ways: every field in these files is read back.
- A push to a Git branch shows up on its Specly branch as pending changes;
  someone reviews and merges them there. A merge, and every edit made in
  Specly, comes back to the branch as a commit from Specly. See "Workflow".
- `.specly.json` is Specly's bookkeeping. Never edit it.

## Layout
- `<tables folder>/[<type>/]<name>.odcs.yaml` — one data contract per table:
                                          the table, its columns, keys and
                                          quality rules
- `<data products folder>/<name>.odps.yaml`  — one Open Data Product Standard
                                          (ODPS v1.1.0) document per data
                                          product
- `Diagrams/<name>.json`               — diagram canvas
- `Config/*.json`                      — registries (data types, flags,
                                          statuses, …). References below use
                                          the `name` field from these.
- `.specly/schemas/`                   — JSON Schema per JSON entity
- `.specly/specly.py`                  — the check: lists what Specly could
                                          not read in (a file of the wrong
                                          shape, a reference to a table or
                                          column that is gone, a table type,
                                          source system, status or flag
                                          missing from its registry in the
                                          repo, a repeated `id`, a layout the
                                          export refuses to write into), what
                                          it would read differently from what
                                          the file says (warnings), and every
                                          file that
                                          is not in the format Specly writes
                                          (a warning; an export copies only the
                                          fields that changed into your file and
                                          never reorders it, see "What the
                                          next export changes"; line endings,
                                          key order and list order do not
                                          count).
                                          Run it before you push (Python 3.9
                                          or newer):
                                          `uv run --no-project --with pyyaml python .specly/specly.py check`
                                          Columns without a description are
                                          counted per file; `--verbose` lists
                                          each, `--strict` makes a format
                                          difference an error. Exit code 0: no
                                          errors; 1: errors; 2: the check could
                                          not run. For a PR build see "The
                                          check in a PR build".
                                          `fix` instead of `check` writes the
                                          files in that format; it changes no
                                          content except what the next export
                                          would write after «Bruk reglene» (see
                                          "Business concepts"). `fix
                                          --add-values` also adds data types,
                                          tags, statuses, table types and
                                          source systems the contracts use to
                                          their registry files (never one that
                                          differs from an entry only in case or
                                          outer spaces: that is reported as a
                                          probable typo). `fix` finishes in
                                          one run (a repaired file is checked
                                          again and the rules written into it
                                          in the same run), never half-writes
                                          a file it cannot finish (errors,
                                          comments: that file is left as it
                                          is; the others are still written),
                                          and keeps each file's line endings.

There are no JSON table or data product files: the contracts are what the
import reads. The project's actual folder names are under
"This project" below. Every `.odcs.yaml` under the root (outside the data
products folder) is read as a table contract and every `.odps.yaml` as a data
product, whoever wrote it — don't keep drafts or third-party contracts here.
A file with this guide's own name in a folder outside the root (the tables
or data products folder) is Specly's: a short pointer to this file. Leave it.
The examples below are what this project's export writes, with its ODCS
settings (see "This project"); their tables, and a table type or field this
project doesn't have, are samples.

## Identity
- A contract's root `id` is the table's stable contract id, frozen the first
  time the table is exported: a slug of its name at that export (whitespace
  and `. # / \ @ ! % & ^` replaced by `_`), or the root `id` of the contract
  it was imported from. A rename after that never changes it, so the root `id`
  can differ from the table name. Root `name` is the table name.
- `schema[0].id` is the table's uuid. `schema[0].properties[].id` is each
  column's uuid. The uuid is the identity: keep it when you rename the table
  or a column, and the rename stays the same table or column.
- Never change an existing `id`. Without it the import can only match the
  table or column by name, so a changed `id` plus a rename becomes a new
  table or column instead of an edit.
- A NEW table or column gets a uuid v4 you generate (e.g. `uuidgen`, lower
  case). The import keeps it as the new entity's uuid. Or write it without
  `id` and run `fix --add-ids --changed-from <base>`: it writes the id the
  import would mint for it (uuid v5 of the project id, the root `id` and the
  names), the same for everyone who runs it, and puts back an `id` the base
  had.
- Table names are unique in a contracts repo: the import reads one contract
  per table name (case-insensitive) and ignores any other with a warning.
- The import matches by uuid first. Only an `id` it doesn't know falls back
  to the name: a table by its name (exact, then case-insensitive), a column
  by its name inside that table. A missing `id` is minted from the root `id`
  and the names. Don't rely on either fallback — write the uuid. Because
  of the fallback, a new table can't share its name with an existing one.
- No export writes a missing `id` into your file: a table or column without
  one stays without, and is known by its name on every pull. Renaming it in
  Git is then a removal plus a new table or column. That is why the check
  warns about it (`lint.uuid.missing`). If more of a branch's tables and
  columns go without an `id` than with one, Specly reads the branch as
  «Kort form» (names as identity), and offers «Nytt filformat» when the
  project's settings write ids.
- Every `id` is unique in the project. Copying a quality rule or a
  relationship into another contract copies its `id` too, and Specly then
  does not take in the contract with the copy until the copy has a new uuid
  v4 (the check reports `lint.uuid.duplicate`). Give the copy the new id,
  never the original: a changed `id` on the one Specly knows reads as one
  rule or relationship deleted and a new one made.

## Recipe: add a table
Create one new file per table, named `<table name>.odcs.yaml` (`æ ø å`
written `ae o a`, every other character other than `A-Z a-z 0-9 - _`
replaced by `_`), in the folder the export uses for that table: the tables
folder, plus the table type's subfolder when this project groups tables by
type (see "This project"). A file anywhere else, or named otherwise, still
imports and stays where you put it (see "Recipe: rename or move a contract
file"); keep it with the others.

- The table type is the `tableType` custom property: a name from
  `Config/table_types.json`. The folder is not read. Without `tableType` an
  existing table keeps its type and a new one gets whatever Specly's table-type
  rules give it.
- `databaseName` and `schemaName` are custom properties too. Set them when
  "Table naming" below says they are required. `servers` is written when
  Specly writes the whole file (a table new from Specly's side, or «Nytt
  filformat»), never added to a contract you wrote; its first entry's
  `catalog`/`schema` is only read for a field the table doesn't set itself.
- `version` is required by ODCS; use `1.0.0`.
- A table type can define standard columns (`columnTemplates` in
  `Config/table_types.json`: name, `dataType`, `flags`). They are not added to
  a table that arrives from Git: its page in Specly warns that standard
  columns are missing and offers a button that creates them. Add them to
  `properties` yourself to avoid that. Copy the naming from an existing table
  of the same type; this repo's own tables may name them differently than the
  template.
- The table object carries `logicalType: object` and `physicalType: table`.
  No table-type field is mapped to `physicalType`, so the import takes a
  schema object as a table only when its `physicalType` is `table` or
  `view`.
- The table status is a name from `Config/table_statuses.json`. The export
  writes it as root `status`: the status's `odcsStatus` (an ODCS lifecycle
  value such as `active`) where it has one, else its name. Only where that
  value can't lead back to exactly this status (another status has it as its
  name or `odcsStatus`) does the export also write the name, as the `status`
  custom property. Either one reads back as the status.
- The table's foreign keys go in its own contract (see "Relationships"). If
  it belongs to a data product, add its name to that `.odps.yaml` (see
  "Data products").

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: orders
name: orders
schema:
  - id: 9e1b5d3a-7c2f-4f86-b4a1-6e0d8c2b9a14
    name: orders
    physicalType: table
    logicalType: object
    properties:
      - id: d2a6f1c8-4e3b-4d79-9f12-8b5c0a7e6d25
        name: order_id
        physicalType: bigint
        logicalType: integer
        description: Order number from the web shop.
        primaryKey: true
        required: true
      - id: e8c3b7a1-5f2d-4a6e-b9d4-3a1f0e8c7b36
        name: customer_id
        physicalType: bigint
        logicalType: integer
        description: The customer who placed the order.
        required: true
        relationships:
          - id: 5b7d9f1a-2c4e-4a68-8b0d-1e3f5a7c9b42
            type: foreignKey
            to: customer.customer_id
            customProperties:
              - property: comment
                value: The customer who placed the order.
              - property: sourceCardinality
                value: zero-or-more
              - property: targetCardinality
                value: exactly-one
    description: One row per order.
    customProperties:
      - property: tableType
        value: raw
      - property: databaseName
        value: analytics
      - property: schemaName
        value: sales
```

## Recipe: add a column
Add one entry to the table's `properties`. The position in `properties` is
the column order — insert it where it belongs, and don't reorder the rest
for cosmetics.

- `id`: a new uuid v4. `name`: the column name, unique within the table.
- `physicalType`: the data type's `name` from `Config/datatypes.json`. If the
  type is new, add it to `Config/datatypes.json` first (omit `uuid` there).
- `logicalType`: the ODCS logical type (`string`, `integer`, `number`,
  `boolean`, `date`, `timestamp`, …) — the datatype's own `logicalType` when
  `Config/datatypes.json` sets one. Not stored per column.
- `logicalTypeOptions`: length, precision, format and so on (ODCS
  vocabulary, e.g. `maxLength`). Without them the column takes its
  datatype's: its `logicalTypeOptions` in `Config/datatypes.json`, else
  `format: binary` for a binary type. Options equal to the datatype's are not
  stored per column.
- `description`: the column description.
- Keys and constraints are flags. `primaryKey: true`, `required: true` and
  `unique: true` each attach the flag in `Config/flags.json` whose `systemKey`
  is `primaryKey`, `required` or `unique` (likewise `partitioned`,
  `criticalDataElement` and `deprecated`).
  A business key is the custom property `businessKey: true`; it attaches the
  flag with `systemKey` `businessKey`.
  In this project a key column is always required (`primaryKeyRequired`):
  when Specly writes a contract whole (a table new from Specly's side, or
  «Nytt filformat») it writes `required: true` next to every
  `primaryKey: true` — it never adds it to a contract you wrote —, and
  the import reads that `required` as part of the key, not as the required
  flag.
- `tags` lists the column's other flags, by flag `name` from
  `Config/flags.json`. A flag with a `systemKey` is never listed there — its
  boolean (or the business key) already carries it. Any other flag is set by
  adding its name to `tags`.
- `businessName`: the column's name in the next layer, its downstream name
  (see "Downstream names and automatic renames"). Leave it out when the name
  stays the same.
- `customProperties` (each `{property, value}`): `status` (a name from
  `Config/column_statuses.json`, written only when its ODCS value
  (`odcsStatus`, else its name) differs from the table's status's; a
  property without it has the table's status. In place of the name goes the
  status's `odcsStatus` (an ODCS lifecycle value such as `active`) where it
  has one. Only where that value can't lead back to exactly this status
  (another column status has it as its name or `odcsStatus`) does the export
  also write the name, as the `statusName` custom property. Either one reads
  back as the status) and one entry per column field of the table's type
  mapped to `customProperties`, named by the field's `odcsPropertyName`,
  else its `key` in `Config/metadata_field_definitions.json` in camelCase
  (`scd_type` becomes `scdType`). A built-in or field mapped to an ODCS key
  goes in that key instead ("Built-in fields" and "Table type fields" under
  "This project").
- `quality` holds the column's data-quality rules (ODCS `quality[]`).
- The column's sources are a list of `<table>.<column>` references (see
  "Column lineage" for where they go). A new column with one source whose
  `name` is the source's downstream name (else the source's name) follows
  that name from then on; give it a name of its own to keep it (see
  "Downstream names and automatic renames").

This adds `phone` to an existing `customer` table. The table and its two
existing columns keep their `id`s:

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: customer
name: customer
schema:
  - id: 3f6c2a1e-8b4d-4c7a-9e21-5d0b7f3a6c11
    name: customer
    physicalType: table
    logicalType: object
    properties:
      - id: a1d4e7b2-3c5f-4a89-b6e0-1f2d3c4b5a61
        name: customer_id
        physicalType: bigint
        logicalType: integer
        description: Surrogate key.
        primaryKey: true
        required: true
      - id: b7e2c9d4-6a1f-4b3e-8d50-2c7a9e1f4b72
        name: email
        physicalType: varchar
        logicalType: string
        description: Login e-mail.
        unique: true
        logicalTypeOptions:
          maxLength: 255
      - id: c4f8a2e6-1b9d-4e57-a3c0-7d6e5f4a3b83
        name: phone
        physicalType: varchar
        logicalType: string
        description: Mobile number in E.164 format.
        businessName: Phone number
        required: true
        transformDescription: Validated with libphonenumber.
        logicalTypeOptions:
          maxLength: 20
        transformSourceObjects:
          - crm_contact.mobile
        customProperties:
          - property: businessKey
            value: true
    description: One row per customer.
    customProperties:
      - property: tableType
        value: raw
      - property: databaseName
        value: analytics
      - property: schemaName
        value: crm
```

## Recipe: change a column
Edit the property in place and keep its `id`.

- Rename: change `name`. The `id` carries the column across (uuid, history,
  lineage). Rename in Specly and the next export writes the new name.
- Names in other files are matched by name, so update them in the same push:
  `to: <table>.<column>` in other contracts and the `transformSourceObjects`
  references downstream.
- New type: change `physicalType` (and `logicalType`/`logicalTypeOptions`
  to match).
- Constraints: add or remove `primaryKey`/`required`/`unique`. Don't add a
  key flag's name to `tags` — `tags` alone also sets a flag, so a name left
  there keeps the flag after its boolean is removed.
- Description: change `description`.

These fields are written on export and never read back — editing them does
nothing: `partitionKeyPosition`, the root `dataProduct`, the per-column
`logicalType`. A column's `businessName` is its downstream name (see
"Downstream names and automatic renames" below) — never a column field or
a concept link.

This renames `email` to `email_address`, changes its type and description,
and drops the unique constraint. Same `id` as before:

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: customer
name: customer
schema:
  - id: 3f6c2a1e-8b4d-4c7a-9e21-5d0b7f3a6c11
    name: customer
    physicalType: table
    logicalType: object
    properties:
      - id: a1d4e7b2-3c5f-4a89-b6e0-1f2d3c4b5a61
        name: customer_id
        physicalType: bigint
        logicalType: integer
        description: Surrogate key.
        primaryKey: true
        required: true
      - id: b7e2c9d4-6a1f-4b3e-8d50-2c7a9e1f4b72
        name: email_address
        physicalType: text
        logicalType: string
        description: Contact e-mail, not used for login.
    description: One row per customer.
    customProperties:
      - property: tableType
        value: raw
      - property: databaseName
        value: analytics
      - property: schemaName
        value: crm
```

## Recipe: reorder columns
The order of `properties` is the column order. Moving entries is a change
like any other: «Fra Git» lists it as a change of the table's column order,
and Specly's export writes the order back the same way. Move whole entries
and keep every `id`.

## Recipe: move a column to another table
- Remove its entry from the old table's `properties` and add it to the new
  table's, with the SAME `id` and every other key (description, flags,
  sources), in the same push. Specly reads it as the same column moved:
  uuid, description, flags and lineage sources stay.
- Update every reference to it in that same push to `<new table>.<column>`:
  `to:` in `relationships` (also composite `from`/`to`), the references in
  `transformSourceObjects` of the columns downstream. A reference left on the
  old `<table>.<column>` is not read.
- Copying is not moving: the same `id` in two entries that both stay gives
  the copy a new id on the pull (see "Editing by hand: what happens").

## Recipe: rename a table
Change the root `name` and `schema[0].name` to the new name; keep the root
`id` and `schema[0].id`. Rename the file to `<new name>.odcs.yaml` (same
character rule as "add a table"); the file's name is not read and Specly
never moves it back. In the same push update every reference that names the
table. Specly shows the change as a rename of the same table (uuid, history,
columns, diagrams and lineage stay):

- `to: <table>.<column>` in the `relationships` of every contract, composite
  `from`/`to` lists included; one left on the old name is not read
- the `<table>.<column>` references in `transformSourceObjects` of the
  columns downstream, and the table's name in `upstreamTables` of other
  tables
- the table's name in a data product's `tables`
- its placements in `Diagrams/*.json`: change `table` and keep `tableUuid`
  (the uuid wins, so a placement left on the old name is harmless, only
  stale)

## Recipe: move a table to another table type
- Change the `tableType` custom property to a name from
  `Config/table_types.json`, and move the file to that type's folder when this
  project groups tables by type (see "This project"). The folder is not read:
  a file left in the old one reads the same and Specly does not move it back.
- The new type's standard columns are not added, as for a new table (see
  "Recipe: add a table").
- A table or column field the new type does not wire in is not shown or taken
  in by Specly: its value stays in the file, and «Fra Git» lists it («feltet er
  ikke koblet til tabelltypen») until the field is linked to the type in
  Specly or the property is removed here.

## Recipe: rename or move a contract file
The table is identified by `schema[0].id`, not by the file's name or folder, so renaming or moving the file changes nothing in Specly and
lists no change. Specly never moves it back: it moves a file only when it
exports a change of its table's name or table type, then to the path "Recipe:
add a table" describes. Move the file, don't copy it: the same table in two
files is reported in «Fra Git» and not read in until one of them is deleted.

## Recipe: change a table's or a column's status
Change the root `status` to a name from `Config/table_statuses.json`: every
column without its own `status` follows the table's new status. To keep a
column on a status of its own, give its property a `status` (a name from
`Config/column_statuses.json`) that differs from the table's new status:
Specly writes a column's status only where it differs from its table's, so
one equal to the table's is the same as none. To let a column follow again,
remove its `status`.

## Downstream names and automatic renames
In this project a column's `businessName` is the name the column has in the
next layer (`columnBusinessNameSource: downstreamName`). It becomes the
column's downstream name in Specly.

- Which columns are renamed: every column in the next layer whose only
  `transformSourceObjects` reference is this column and whose link is on. It
  gets the source's `businessName`, or the source's `name` when
  `businessName` is missing. The rename carries on down the chain while the
  next links are also on. A column with two or more references is never
  renamed.
- Whether a link is on: when a pull creates the link, Specly derives it from
  the names — on when the column's `name` is the source's `businessName`
  (or the source's `name` when `businessName` is missing), off otherwise. A
  link someone turned off or on in Specly keeps that setting on later pulls.
  The contract never states it.
- When: in Specly, as soon as the source or the link changes — a pull from
  Git included. The renamed column reaches Git on the next export, and the
  `transformSourceObjects` references in other contracts are rewritten in
  the same export.
- A column that keeps its name in the next layer has no `businessName`. A
  `businessName` equal to the column's own `name` is read as empty.
- Specly never renames a column whose `name` differs from its source's
  `businessName` (or `name` when `businessName` is missing) at the time of
  the change: a take-in that rewrites a contract without touching names
  writes such a link off. The state is not in the contract: in Specly it is
  the auto-translation toggle of the column's lineage, and from Git you see
  it through the names alone (compare the column's `name` with the source's
  `businessName`). To turn a rename off from Git, give the column in the
  next layer a name of its own: a link is on only while the names match. An
  `isAutoTranslated` an older export wrote is ignored on a pull, and the
  next full rewrite of the contract drops it.
- Equal names: a rename that would give one table two columns of the same
  name is not made. The column keeps its name and its link is turned off, so
  a name freed later does not rename it. The pull review lists such a rename
  before you take it ("Navnet er i bruk"), also when the pull changes only
  the source, and Specly marks the column's link. A table that still has two
  columns of the same name (an edit in Specly) is held back from the export:
  its own contract stays as Git has it, and other contracts keep naming its
  columns as Git does until the name is fixed.

Here `kunde_nr` is renamed to `customer_number` in the next layer,
`kundemarked_nr` keeps its name because its link is off, and `epost` keeps
its name because it has no `businessName`:

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: cle__crm__customer
name: cle__crm__customer
schema:
  - id: 6a2d8f4c-1e7b-4c39-a5d2-9b0e3f7c1a54
    name: cle__crm__customer
    physicalType: table
    logicalType: object
    properties:
      - id: 7b3e9a5d-2f8c-4d4a-b6e3-0c1f4a8d2b65
        name: kunde_nr
        physicalType: bigint
        logicalType: integer
        businessName: customer_number
      - id: 8c4f0b6e-3a9d-4e5b-87f4-1d2a5b9e3c76
        name: kundemarked_nr
        physicalType: varchar
        logicalType: string
        businessName: customer_market
      - id: 9d5a1c7f-4b0e-4f6c-98a5-2e3b6c0f4d87
        name: epost
        physicalType: varchar
        logicalType: string
```

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: enr__crm__customer
name: enr__crm__customer
schema:
  - id: 0e6b2d8a-5c1f-4a7d-a9b6-3f4c7d1a5e98
    name: enr__crm__customer
    physicalType: table
    logicalType: object
    properties:
      - id: 1f7c3e9b-6d2a-4b8e-8ac7-4a5d8e2b6f09
        name: customer_number
        physicalType: bigint
        logicalType: integer
        transformSourceObjects:
          - cle__crm__customer.kunde_nr
      - id: 2a8d4f0c-7e3b-4c9f-9bd8-5b6e9f3c7a10
        name: kundemarked_nr
        physicalType: varchar
        logicalType: string
        transformSourceObjects:
          - cle__crm__customer.kundemarked_nr
      - id: 3b9e5a1d-8f4c-4d0a-acf9-6c7f0a4d8b21
        name: epost
        physicalType: varchar
        logicalType: string
        transformSourceObjects:
          - cle__crm__customer.epost
```

## Column lineage
- A column's sources are its `transformSourceObjects`: a list of ODCS
  shorthand references `<table>.<column>`, in order. There is no `order`
  field; the first reference is the first source. A column marked as below
  keeps its entries in the `upstreamColumns` custom property instead, since
  `transformSourceObjects` holds only references.
- Where two tables share the source table's name, the reference is
  `<databaseName>.<schemaName>.<table>.<column>`.
- A source table or column with a space or a `.` in its name, or a shared
  table name without `databaseName` and `schemaName`, can't be named in a
  reference: the table is held back from the export, with a warning naming
  the column and the reference, until it is fixed in Specly.
- A contract never states `isAutoTranslated`: Specly derives whether a link
  renames from the names (see "Downstream names and automatic renames"). A
  column with two or more sources is never renamed.
- An older export's `isAutoTranslated` custom property and
  `{column: <reference>, isAutoTranslated: <true|false>}` entries are still
  read as their references, and so are `{sourceTable, sourceColumn, order}`
  entries; the value itself is ignored.
- A table's upstream tables (the table-level list on its page in Specly) are
  the source tables of its columns' lineage and the table's own
  `upstreamTables` custom property: a list of the other ones, `<table>`
  references (`<databaseName>.<schemaName>.<table>` where two tables share
  the name), sorted. The export leaves it out when the columns name every
  one. On a pull the table's list becomes exactly these, so remove a table
  from that list to take it off. A name no table has is reported and
  skipped.

## Recipe: delete a table or a column
Delete the table's `.odcs.yaml` file, or remove the column's entry from
`properties`. Nothing is deleted in Specly until someone applies it there —
see "Deletes" below for exactly when. Before you delete a table, remove every
other reference to it in the same push: the `relationships` of other
contracts that point at it, its placements in `Diagrams/*.json`, its name in a
data product's `tables`, and any `transformSourceObjects` reference to it. A removal
that a relation still points at is refused (see "Deletes").

## Merging your own data into this repo
The biggest risk is a duplicate: the same table or column added a second
time as something new. For every table in your own data:

1. Look for an existing contract first: same table name (and the same
   `databaseName`/`schemaName`) in `schema[0].name`, anywhere under the tables
   folder.
2. Found: edit that file. Keep its root `id`, `schema[0].id` and every
   existing property `id`. For each of your columns, look for a property
   with the same name; found, edit it in place and keep its `id`.
3. Never create a second file for a table that already has one. The import
   reads only one contract per table name (the file named after the table,
   else the first by path) and ignores the other with a warning.
4. Generate a new uuid v4 only for a table or column that really is new.
5. Push, and check the merge review in Specly: an existing table or column
   must never show as new. If one does, fix its `id` and push again.

## Relationships
A foreign key lives in exactly one place: the contract of its `from` table.
There is no `Config/relations.json` in a contracts project (one left by an
older export is ignored, and deleted by the next export). A `Diagrams/*.json`
file keeps only each relation's drawn route, under `relationBreakpoints`
(relation uuid → `breakpoints`); a `relations` list an older export left
there is ignored, and dropped by the next export.

Each relation is written once, as in the `orders` example under "Recipe: add
a table":

- A single-column foreign key is one entry of its `from` column's
  `relationships` (`schema[0].properties[]` level): `type: foreignKey` and
  `to: <table>.<column>`, the referenced table's and column's names.
- A composite key is one entry of the table's `relationships` (`schema[0]`
  level): `type: foreignKey`, and `from` and `to` lists of
  `<table>.<column>` references, in pairs.
- A table or column whose name can't stand in a reference — a name that
  isn't a plain identifier (a letter or `_` first, then only letters,
  digits, `_` and `-`), or one another table (for a column, another column
  of the same table) carries too, compared case-insensitively — is
  referenced as `schema/<table>/properties/<column>` instead, that segment
  its `id` and the other its name.
- `id`: the relation's uuid. Keep it: pointing `to` (or `from`) at another
  column while the `id` stays keeps the same relation, with its drawn route
  in diagrams. A relation you write by hand may leave `id` out: the import
  matches it by its endpoints, or gives it a uuid. No export writes that
  `id` in, so without it changing an endpoint makes it a different relation.
- `customProperties`: `comment`, `sourceCardinality`, `targetCardinality`
  (`exactly-one`, `zero-or-one`, `one-or-more`, `zero-or-more`). Leave one
  out to clear it.

To remove a relation, remove its entry.

A relationship does not set a flag on the `from` column: if your columns carry
a foreign-key flag (a flag in `Config/flags.json`, e.g. `FK`), add its name to
the column's `tags` yourself.

## Metadata field types
A field's `fieldType` in `Config/metadata_field_definitions.json` decides
what its value is and how a contract writes it. As a `customProperties`
entry:

| `fieldType` | In Specly | In the contract |
|---|---|---|
| `kort_tekst` | Short text | A string. With `isMultiSelect`: a list of strings |
| `lang_tekst` | Long text | A string (a multi-line one as a `\|-` block) |
| `tall` | Number | A YAML number: `7`, `3.5` |
| `int` | Integer | A YAML number: `42` |
| `decimal` | Decimal | A YAML number: `3.5` |
| `dato` | Date | `YYYY-MM-DD` |
| `timestamp` | Date and time | `YYYY-MM-DDTHH:MM` |
| `klokkeslett` | Time of day | `HH:MM` (quoted: `'09:30'`) |
| `boolean` | Yes/no | `true` or `false` |
| `person` | A person | The person's `name` |
| `kildesystem` | A source system | The source system's `name`. With `isMultiSelect`: a list of names |
| `nedtrekksmeny` | Dropdown | One of the field's `dropdownOptions`. With `isMultiSelect`: a list of them |
| `tabell` | Another table (table fields only) | The table's `name`. With `isMultiSelect`: a list of names |
| `kolonne` | Another column of the same table (column fields only) | The column's `name`. With `isMultiSelect`: a list of names |
| `beregning` | A calculation built from a fixed block (column fields only) | A map: `kloss` and the columns it reads as `table.column` (see below) |

A field without `fieldType` is short text.

A field may carry a `description`: plain-text help text (it may span lines), shown
next to the field in Specly wherever it is filled in. It is not exported to the
contract; leave it out when there is none.

A field may also carry `labelEn`, its English name: Specly shows it instead of `label`
when the app is in English. `label` stays the name in the other language and the one
the contract uses; leave `labelEn` out when there is none.

A single-select dropdown field may carry `defaultValue`, one of its options: Specly
gives it to new columns made in Specly and to empty table fields when a table gets a
type. Contracts hold the value itself like any other, so they read the same without
the definition; leave `defaultValue` out when there is none.

- Numbers: a value in a number field (`tall`, `int`, `decimal`) is written
  as a number, never as a string. A value that isn't a number (`about 7`) is
  written as the text it is. A short-text field always writes a string, so
  `7` stored there is written `'7'`: to get a number, change the field's
  `fieldType`, not the value.
- `boolean` writes `true` or `false` only. A value that is neither is not
  written at all.
- `person` and `kildesystem` are written as names and read back by name, so
  the name must be in `Config/persons.json` or `Config/source_systems.json`:
  add it there in the same push or before (an entry added in the same push
  resolves; if that file does not exist in the repo yet, Specly has not
  written it — create it as a JSON list of `{"name": …}` entries, with a
  `uuid` v4 each, see "Recipe: change a registry entry"). A name that is in
  neither Git nor Specly is not read in: it stays in the file, and «Fra Git»
  lists it as something to fix in Git. A person or source system that no
  longer exists is left out. To delete one, remove its uses (every field
  value naming it) in the same push.
- `tabell` and `kolonne` point at a table or column, not at its name: Specly
  follows a rename, and writes the current name. They are read back by name:
  a `tabell` value must be a table of the project (in Git or in Specly), a
  `kolonne` value a column of the same table. A name that is neither is not
  read in (Specly lists it under «Fra Git»), and stays in the file as it is.
  A table or column that no longer exists is left out. In
  `Config/metadata_field_definitions.json` a `tabell` field has
  `entityTypes: ["tableType"]`, a `kolonne` field `["column"]`.
- `beregning` says how a column is computed without SQL: `kloss` names one of
  Specly's fixed building blocks, `kolonner` the columns it reads (each
  `table.column`, a column of a table upstream), `valg` its other choices.
  The `naar` block has `betingelser` instead, a list of conditions (`kolonne`,
  `er`, and `verdi` where the comparison takes one), each but the first with
  `ord: og` or `ord: eller` in front; `og` binds tighter. The `fri` block has
  `sql`, hand-written for one platform, which Specly cannot check. The
  `regnestykke` block has `ledd`, a list of terms (`operator` and `kolonne`,
  a `table.column`). Specly
  writes the members in a fixed order and reads them in any. A column it
  names that is in neither Git nor Specly makes the whole calculation unread:
  it stays in the file and «Fra Git» lists it. The code generator of the
  project turns a block into SQL; Specly holds no SQL for the blocks. In
  `Config/metadata_field_definitions.json` a `beregning` field has
  `entityTypes: ["column"]`. The type is switched on per Specly
  environment: where it is off, Specly refuses a config file that defines
  such a field and says so.

  ```yaml
  customProperties:
    - property: beregning
      value:
        kloss: gange
        kolonner:
          a: silver__timeforing.timer
          b: silver__timeforing.timesats
  ```

  Blocks and their members: `janei`, `harverdi`, `store` (`kolonner.kolonne`);
  `erlik`, `standard` (`kolonner.kolonne`, `valg.verdi`); `verdihvisja`
  (`kolonner.naar_ja`, `kolonner.verdi_fra`); `pluss`, `minus`, `gange`,
  `dele`, `prosent` (`kolonner.a`, `kolonner.b`); `avrund`
  (`kolonner.kolonne`, `valg.desimaler`); `tidmellom` (`kolonner.fra`,
  `kolonner.til`, `valg.enhet`: `timer`, `minutter` or `dager`); `delavdato`
  (`kolonner.dato`, `valg.del`: `aar` or `maaned`); `forste`
  (`kolonner.forst`, `kolonner.ellers`); `slasammen` (`kolonner.forst`,
  `kolonner.saa`); `naar` (`betingelser`, `valg.resultat` and the members under it below;
  `er` is one of `ja`, `nei`, `lik`, `ulik`, `storre`, `mindre`, `fylt`,
  `tom`); `regnestykke` (`kolonner.forst` and `ledd`); `lokaldato`
  (`kolonner.tidspunkt`, `valg.tidssone`); `fri` (`sql`).

  What the new and widened blocks mean, so SQL can be generated from them
  (a quoted text is written as an SQL string literal with `'` doubled; a
  `table.column` is that column of the upstream table):

  - `regnestykke`: `kolonner.forst` is a number column, `ledd` an ordered list
    of at least one term. Each term has `operator` (`pluss`, `minus`, `gange`
    or `dele`) and `kolonne` (a number column). It is evaluated strictly from
    left to right, with no operator going before another: with `forst` a and
    terms `gange` b, `minus` c the value is `(a * b) - c`, and `a minus b
    gange c` is `(a - b) * c`. Write the parentheses the order needs: each term
    wraps what is before it, `((a * b) - c)`. A term with `dele` gives an
    empty value (null) when its column is 0, as the `dele` block does, and an
    empty value in any column makes the whole result empty. Gives a number.
  - `lokaldato`: `kolonner.tidspunkt` is a timestamp column, `valg.tidssone`
    one of `Europe/Oslo` (the default), `UTC`, `Europe/London`,
    `Europe/Stockholm`, `Europe/Copenhagen`, `Europe/Helsinki`,
    `Europe/Berlin`, `Europe/Amsterdam` (IANA names). The stored timestamp is
    read as UTC (it has no zone of its own); the value is the calendar date
    of that instant in the time zone, as a date: `2026-03-28T23:30` in
    `Europe/Oslo` is the date `2026-03-29`. Gives a date, not a timestamp.
  - `naar` with `valg.resultat`: absent (or `tall`) gives a number as before:
    `kolonner.saa` when the conditions hold (1 when `saa` is absent), else 0.
    `janei` gives true when the conditions hold, else false (a boolean, never
    1/0; `kolonner.saa` is not used). `tekst` gives the text `valg.tekst_saa`
    when the conditions hold, else the text `valg.tekst_ellers`; both are
    always present and are literal text, not column names (`kolonner.saa` is
    not used). With `janei` and `tekst` the result is a boolean or a text, so
    it fits a column of that datatype.
- `isMultiSelect` applies to `kort_tekst`, `kildesystem`, `nedtrekksmeny`,
  `tabell` and `kolonne`.
  Its list is written even when it holds one value.
- A field mapped to an ODCS key instead of `customProperties` takes that
  key's own type (a date in `contractCreatedTs`, a list in `tags`, …).

```
customProperties:
  - property: rowCount        # int
    value: 42
  - property: isPersonalData  # boolean
    value: true
  - property: reviewedOn      # dato
    value: '2026-11-06'
  - property: loadTime        # klokkeslett
    value: '09:30'
  - property: owner           # person
    value: Kari Nordmann
  - property: sources         # kildesystem, isMultiSelect
    value:
      - SAP
      - CRM
  - property: layer           # nedtrekksmeny
    value: Gold
  - property: replacedBy      # tabell
    value: cur__f__salg_ordre
```

## Contract key order
Keys are matched by name, so a contract whose keys are in another order means
the same. An export keeps your file's key order: it changes the value of a
key in place, and a key it adds goes right before the next key of the list
below that your file has. Only a contract Specly writes whole because the table
is new from Specly's side gets the keys Specly sets in this order, then any key
Specly has no concept of. «Nytt filformat» leaves a file that equals Specly's
as values alone, and in a file it does rewrite keeps your key, list and tag
order. `check` never reports key or list order, and `fix` never changes it. At the document root: `apiVersion`, `kind`, `version`, `id`,
`name`, `tenant`, `status`, `servers`, `dataProduct`, `domain`, `schema`,
`contractCreatedTs`, `slaProperties`, `support`, `team`, `customProperties`.
In a `schema` entry: `id`, `name`, `physicalType`, `logicalType`,
`properties`, `description`, `businessName`, `tags`, `physicalName`,
`dataGranularityDescription`, `deprecated`, `synonyms`, `context`,
`customProperties`, `relationships`, `quality`. In a property: `id`, `name`,
`physicalType`, `logicalType`, `description`, `businessName`, `primaryKey`,
`required`, `unique`, `partitioned`,
`partitionKeyPosition`, `criticalDataElement`, `deprecated`, `physicalName`,
`semanticType`, `classification`, `encryptedName`, `transformLogic`,
`transformDescription`, `synonyms`, `examples`, `enum`, `tags`,
`relationships`, `logicalTypeOptions`, `transformSourceObjects`,
`customProperties`, `quality`. A key position that follows `primaryKey` (see
"ODCS settings") comes right after it. Array order is data: a new column goes
where you put it in `properties`.

## Editing by hand: what happens
An export does not write a contract from Specly's model: it copies the fields
that changed in Specly into your file's text and leaves every other byte as
it is (comments, key order, quoting, keys Specly does not know). So a value
Specly reads differently from what the file says (a warning of the check)
stays in the file until that field changes in Specly.

- Rename a column and keep its `id` line: the same column, with its
  description, lineage, flags and metadata. Change every `to:` that names
  it, in other contracts too, in the same push: one left on the old name is
  not read (see the last point).
- Add a column without an `id`: Specly matches it by its name, or gives it a
  uuid on the pull. No export writes that `id` into the file: until you
  write one, the name is its identity, and renaming it in Git is a removed
  column plus a new one.
- Delete a column's `id` line: the column is matched by its name, and no
  export writes the `id` back. Rename it in the same push, or later, and it
  is a removed column plus a new one.
- Copy a column with its `id` line: the copy gets a new id on the pull, and
  «Fra Git» warns about it. The original is unchanged.
- Rename in Specly: the next export writes the new name in the file and in
  every `to:` that names it.
- Add a relation: write `to: <table>.<column>` in the column's
  `relationships`. Specly finds the table and column by name, in other
  contracts too. This is the only form written. A composite key is one entry
  of the table's `relationships`, with `from` and `to` lists of
  `<table>.<column>`, in pairs. Leave out its `id`: Specly matches the
  relation by its endpoints, or gives it a uuid on the pull; no export
  writes that `id` into the entry, so changing an endpoint later makes it a
  different relation.
- Remove a relation: remove its entry. The relation is only there.
- Change what a relation points at and keep its `id` line: it stays the same
  relation, with its comment, cardinalities and drawn route in diagrams.
- Point a reference at a table or column that doesn't exist (a typo, or a
  name changed in this push): the relation is not read. «Fra Git» lists
  the file under «Må rettes i Git» with «… som ikke finnes i Specly.
  Rett referansen i Git, og hent på nytt.» Fix the reference in Git and
  pull again.

**Which style** (`referenceStyle`, Admin → ODCS → «Referanser i
kontrakten»): «Id-er, navn i referanser» (`namedRefs`) suits most repos.
Tables, columns and relations keep their uuid, so a rename or a new target
in Git keeps the description, lineage, flags, metadata and the drawn route
in diagrams, and each relation is written in one place. Its cost: one `id`
line per table, column and relation, and a column renamed in Git without its
`to:` elsewhere loses those foreign keys until they are fixed. «Kort form»
(`shorthand`) suits files written by hand whose names seldom change.

## The rules in Config: what a run would change
Flag rules, column sorting rules and relation rules never run by themselves
in Specly: a user runs them (Specly offers it after a take-in). A `rules.*`
finding describes what running the rules in Specly would change, not what
the next export changes. `fix` writes nothing for them; `fix --apply-rules`
does in Git first what a run of the flag rules and column sorting rules
would do, only where the outcome is certain (relations and renames are
check-only). The findings are always warnings (`--fail-on rules.sort` makes
them stop a PR). With `--changed-from` they cover what the push can change
in a run: flags for a column the push adds, renames (or whose table it
renames), or gives other tags or constraint keys; sorting for a table whose
name, column list, `excludeFromSorting`, or a column's datatype, tags or
constraint keys the push changes; relations with a changed table at one end.
A push that changes what the rules read is checked for every table that rule
kind reads, and those findings name the config files, so they show: a changed
rules file or `odcs.json` (formatting alone does not count), or an entry of
`flags.json` or `datatypes.json` a rule names (by uuid or name) that the push
adds, removes or changes. A new flag or data type no rule names widens
nothing; a new data type a column uses, under a `datatype_group` rule, brings
in that column's table. A registry value the push removes or renames shows
the `lint.enum.*` finding in every contract that still uses it; a value it
adds shows nothing new. What the files alone do not decide is reported as `undetermined` and
never written. A rule pattern counts only when Python and Specly's Rust regex
are sure to read it alike: literal text, `\d \w \s \b` and their capitals,
escaped punctuation, `.`, `^`, `$`, `|`, groups `(...)` and `(?:...)`,
character classes without nested classes, `&&`/`--`/`~~` or `[\b]`, `* + ?`
(also lazy), `{m}`, `{m,}`, `{m,n}` on a single character or class with the
numbers adding up to at most 100 in the pattern, a pattern of at most 200
characters (Rust refuses a pattern that compiles too large, `\w{250}` for
one, and then the rule matches nothing), and `(?i)` at the start. Anything else
(lookaround, backreferences, `\p{...}`, `{,n}`, other `(?` groups) is
`undetermined`. The engines also differ on some characters: with `\w \b \s
\d` (and their capitals), or when case does not count (`(?i)`, and every
sorting pattern), a name with a character outside printable ASCII and the
Latin-1 letters (`æ ø å é ü` ...; not `ß`, `ÿ`) makes that column's or
table's outcome `undetermined` (`²` is `\w` in Python, not in Rust; `å`
written as `a` plus a combining ring is `\w` in Rust, not in Python; `ı`,
`İ`, `ſ` and the Kelvin sign fold differently).

- **Flag rules** (`Config/flag_rules.json`, `rules.flag.wouldAdd`): each
  active rule over every column; a run only adds flags (`removeUnmatched`
  is ignored). `startsWith`/`endsWith`/`contains` match the pattern as plain
  text, `regex` as a regex, all case-sensitive on the column name;
  `tableNamePattern` is a case-sensitive regex on the table name; a blank
  pattern matches nothing. A column already has a flag when one of its
  `tags` names it or its constraint key is `true` (`primaryKey`, `required`,
  `unique`, `partitioned`, `criticalDataElement`, `deprecated`, by the
  flag's `systemKey` in `flags.json`), or the business key stands where
  `odcs.json` sends it. A flag that `odcs.json` ties to a column
  `customProperties` entry (a leaf with `source: {"kind": "flag"}`) is
  written in that entry, never as a tag; the column has it when the entry
  says `true` there, and a rule that would give it is `undetermined`
  (`fix --apply-rules` does not write the entry). A primary key with `required: true` while
  `primaryKeyRequired` is on holds the Required flag only if Specly already
  gave it that flag; the files do not say, but the export writes the same
  `required: true` either way, so a rule giving it Required changes nothing
  in the file and is not reported. `undetermined`
  (`rules.flag.undetermined`): a rule without `isActive`, a flag not in
  `flags.json`, a pattern outside the subset above, a name the subset's
  characters do not cover.
  `fix --apply-rules` writes what the export writes after the run: a
  constraint flag as `<key>: true`, or a new `tags` list, in front of the
  first key after it in Specly's order that the column has and Specly itself
  writes (Specly writes `customProperties` only with an entry it knows: a
  built-in sent there by `odcs.json`, a column metadata field, a legacy
  key; an entry like `foo` it keeps but does not write, nor `downstreamName`
  when `columnBusinessNameSource` is `downstreamName`; a column status it
  writes only when it differs from the table's, and the sources only when
  each one exists, so with those the files do not decide), and at the end of
  the column when there is none, so after `customProperties` or `quality`
  Specly does not write (`primaryKey: true` also adds `required: true`
  unless `primaryKeyRequired` is `false`). Any other flag is a tag appended
  to the column's `tags`. It does not write
  (check-only) a primary key when the project numbers its key columns (the
  export renumbers them), a business key, a partition flag, a key the column
  already has with another value, more than one new tag on a column (Specly
  loads the flag rules in no fixed order, and the export writes new tags in
  that order), a column with a later key whether Specly writes is not
  decided by the files (`relationships`, an odd `customProperties` or
  `quality`), or a contract with more than one table in `schema`. A flow
  list (`tags: [A]`) is written as a block list first, in the same run;
  with `--ignore format.differs` that column is check-only.
- **Column sorting rules** (`Config/column_sorting_rules.json`,
  `rules.sort.wouldReorder`): the active rules by descending `priority`,
  each a stable sort, so the rule with the lowest priority decides and the
  others break its ties. `alphabetical` sorts case-folded with `æ`, `ø`,
  `å` after `z`, `-`/`_`/space before digits before letters (`direction:
  desc` reverses it); `pattern_first`/`pattern_last` move the columns whose
  name the case-insensitive pattern finds; `datatype_group` moves the
  columns of that datatype first (a column's datatype is its `physicalType`,
  else its `logicalType`, as the take-in reads it); `flag_order` sorts by the first listed
  flag a column has. A table whose `excludeFromSorting` is true is skipped
  (it is read on the table only; on a column Specly ignores it, and `check`
  says so).
  The order the run starts from is the file's `properties` order: that holds
  when the file is what Specly holds. `undetermined`
  (`rules.sort.undetermined`): two active rules with the same priority
  (their order is the order they were made in Specly), a rule without
  `isActive`, a datatype or flag not in the registries, a column datatype
  not in `datatypes.json` under a `datatype_group` rule, a `flag_order`
  table where a flag rule would add a listed flag or that lists Required
  with a primary key holding `required: true`, a pattern outside the subset
  or a column name its characters do not cover. With no active rule a run sorts every table by name; `check` does
  not report that. `fix --apply-rules` moves whole column entries, from the line with
  `-` to the end of the entry, the way the export moves them; it leaves a
  file with comments, or with more than one table in `schema`, alone and
  says so.
- **Relation rules** (`Config/relation_rules.json`,
  `rules.relation.wouldCreate`): one warning per rule, with the count and
  the first five pairs. A pair counts when no relationship in the contracts
  joins the two columns in either direction. With `--changed-from`, only
  pairs with at least one table in a changed file. `fix` never writes a
  relation: Specly gives a new relation its own id, and a relation that
  exists only in Specly stops a match.

More than ten `rules.flag.wouldAdd`, `rules.flag.undetermined`,
`rules.sort.wouldReorder` or `rules.sort.undetermined` findings show as one
line with the count, also when `--fail-on` makes them errors (the exit code
is the same); `--verbose` and `--json` list each.

**Automatic renames** (`lineage.autoRename`, only with `--changed-from`):
when a push changes a column's name or downstream name, the name Specly
derives for the columns it feeds changes (the trimmed downstream name, else
the name). When the push is taken in, Specly renames each column that is
translated automatically from it (a take-in runs this as an edit in Specly
does), unless the target table already has a column with exactly the new
name: then it turns the automatic translation off instead. A column whose
lineage entry says `nameDirection: toSource` is never renamed this way. A
column with more than one source is renamed only when it is marked as a
deviation from the single-source rule in Specly; that mark is not in Git,
so `check` leaves every such column out and may miss one Specly renames. The next export writes the
new names, and the `transformSourceObjects` of the columns that cite them.
`check` lists the columns citing the source that carry the old derived
name. Whether a column is translated automatically is not in Git, so it
says "can be renamed"; `fix` does nothing here.

## What the next export changes in a file you wrote by hand
A file with no `check` errors is read in (its warnings say where Specly
reads something otherwise than the file says it). After someone takes it in
with «Hent inn», the next export changes it only for one of these:
- An edit made in Specly to that table, column or relation (in that field
  only, in your file's quoting).
- «Bruk reglene» on business concepts: new concept links in the concept
  file, and the concept's text in a linked column's empty fields. `check`
  reports both (`lint.concept.*`) and `fix` writes them first.
- A concept file without `uuid`: the export adds it (`lint.concept.noUuid`;
  `fix` writes it).
- A column in the next layer renamed automatically from its source (see
  "Downstream names and automatic renames"), and the references to it.
- A flag added or removed in Specly (in the UI or by a flag rule): that tag
  goes into or out of the column's `tags` in place, your order kept.
- A run of the flag rules or column sorting rules in Specly, if someone runs
  them (see "The rules in Config"): `check` reports what it would change
  (`rules.*`), and `fix --apply-rules` writes what is certain.
- «Nytt filformat» (after an ODCS or layout setting changes): a contract
  the new settings change as values is written in Specly's layout, with your
  key, list and tag order kept; one that equals Specly's as values (only
  order, quoting or indents differ) is left as it is.
- A registry entry (`Config/*.json`) changed in Specly: that whole file is
  written again in Specly's layout (see "Key order" in the shared part). An
  entry you added without `uuid` stays as you wrote it, still without
  `uuid`, and is sorted as if its uuid were empty: among the entries without
  an order field it comes first. `fix --add-values` instead writes a new
  entry with the uuid Specly derives from the name, at the place Specly
  sorts it, so the next export leaves it as it is.
- A data type, tag or status added to its registry: the export after the
  take-in adds its name to `.specly/lint.json` (Specly's file; `fix
  --add-values` writes it there too).
- A file the export's patcher cannot parse as YAML (very rare; a layout
  that other YAML readers take): its changed fields go into your content
  written out in Specly's layout, comments lost. This applies only to such a
  parse error, not to the layouts below.

The export refuses a file — it stops, writes nothing, and says which file —
when it must write a change into a part of the file whose layout it cannot
write into. Each layout blocks only the edits listed with it; other changes
to the same file go through. Specly reads these files correctly, so only an
export carrying such an edit shows it. `check` reports each as an error
(`export.refused`), naming the edit it blocks:
- a YAML anchor or alias (`&name`, `*name`) anywhere in a contract or data
  product blocks every edit in the file: write the value out at each place
  (`fix` does, in a file without comments);
- a table or column written in flow style (`- {id: ..., name: ...}`) blocks
  an edit of that table's or column's fields: write it as a block, one key
  per line;
- a list of tables, columns or quality rules in flow style
  (`properties: [...]`) blocks adding a table, column or rule to it: write
  it as a block;
- a list of tables, columns or quality rules whose FIRST item has the `-`
  alone on its line and the keys below it blocks adding an item to that
  list (the new item copies the first item's layout; a later item laid out
  so is fine): put the first key on the `-` line;
- `name`, `description`, `physicalType` or `logicalType` of a table or
  column (or the contract's `id`, `name`, `dataProduct`) with nothing after
  the colon (`description:`), or with a list or mapping as value, blocks an
  edit of that field: write `""` or `null`, or remove the key;
- `transformSourceObjects` or a lineage value in `customProperties` as a
  flow list over several lines blocks taking out a source whose column or
  table was deleted in Specly (it is removed item by item; any other edit
  of the list rewrites it as a block): write it on one line or as a block.

A flow list on one line (`tags: [a, b]`), a flow-style entry elsewhere (a
`customProperties` entry), block scalars (`|`, `>`), comments and any quoting
are fine: the export writes into them, or rewrites just that entry in block
style.

It never changes a file for these alone: a missing `id` (the item is matched
by its name, see "Identity" — renaming such an item in Git is a removal plus
a new item), a missing `servers` or `required`, key order, quoting, indents
or line endings, or the order of tags.

### Tag order
A column's tags are a set: a push that only reorders them is no change, and
Specly keeps its own order for them. That order is how the flags reached the
column, not `Config/flags.json`'s `order`: a table new from Git keeps the
order of its `tags`; a take-in that changes the set of tags of a column
Specly already holds stores them sorted by name (byte order: capitals
first); a flag added in Specly or by a flag rule goes last. When Specly writes a new column whole it writes
that order, the business key first; a column in your file keeps your order,
also at «Nytt filformat». `check` never reports tag order.

## The check in a PR build
`check` exits 0 when it finds no error, 1 when it finds one, and 2 when it
could not run (an unknown `--changed-from` ref, a shallow clone without the
common ancestor — check out with `fetch-depth: 0` —, git failing, pyyaml
missing, a broken `.specly.json` or `.specly/check.json`, or an error in the
script, a Python older than 3.9; `--verbose` prints the traceback of an
error in the script). Treat 2 as a broken build, not as findings.

    uv run --no-project --with pyyaml python .specly/specly.py check --changed-from origin/main

- `--fail-on <code>` makes a warning with that code an error (exit 1), e.g.
  `--fail-on lint.uuid.missing`. A code also matches the codes it is a
  dot-separated prefix of: `--fail-on lint.enum` covers every registry
  finding (`lint.enum.dataType`, the only one that is a warning, …), but
  not `lint.enumx`.
  (`lint.enum.` and `lint.enum.*` mean the same.)
- `--ignore <code>` hides warnings with that code and leaves them out of the
  counts. An error is hidden only when its whole code is named, never by a
  prefix. A code named in both `failOn` and `ignore` fails: `failOn` wins.
- A code that matches nothing the check reports (a typo such as
  `lint.column.noDescriptoin`), or an empty one, stops the check with exit 2
  and says so — from the command line and from `.specly/check.json` alike —
  so a typo cannot turn the build green.
- Both can be repeated, and work with `--json` (which then also has
  `failOn` and `ignored`) and `--changed-from`. `fix --ignore <code>` leaves
  what that code reports alone.
- Team defaults go in `.specly/check.json`, a file Specly never writes or
  deletes: `{"failOn": ["lint.uuid.missing"], "ignore": ["lint.column.noDescription"]}`.
  Flags on the command line add to it. `.specly/lint.json` is Specly's: the
  export writes it again, so do not put settings there. `check.json` decides
  what stops a PR — an `ignore` of a whole error code even lets an
  unreadable file pass with exit 0 — and a PR can change `check.json`
  itself: protect it (a CODEOWNERS entry, or a branch policy that requires
  the owners' review for `.specly/check.json`). If it exists but is not a
  readable file, the check stops with exit 2.
- With `quoteAllStrings: false`, `fix` writes a quoted `'2024-01-01'`, `'yes'` or
  `'on'` plain: the same text for Specly (YAML 1.2), but a YAML 1.1 reader in the
  repo (PyYAML, datacontract-cli) then reads a date or a boolean.
- `--strict` makes `format.differs` an error. It is only a difference of
  layout: Specly reads the file as written.

## Data products
Each `.odps.yaml` is one data product. Its identity is the `speclyId` custom
property (the data product's uuid; keep it, and give a new data product a new
uuid v4); the root `id` is frozen at the data product's first export, like a
table contract's, and a later rename never changes it. Read back on import: `name`,
`status` (a name from `Config/data_product_statuses.json`, or the
`odcsStatus` lifecycle value one of them maps to, as the export writes it), `version`,
`team.name` (the owner), `description.purpose`/`.limitations`/`.usage` and
the other slots an admin mapped a field to, and the member lists. Members are
the `tables` custom property, a list of table names (and `diagrams`, a list
of diagram names) — add or remove a table there, not in the table's contract
(a contract's `dataProduct` is never read back). Removing a table's name from
`tables` takes it out of the product (the table stays); deleting the
`.odps.yaml` removes the data product in Specly once someone takes it in (its
tables stay). A member that names a table Git does not have is listed under
«Må rettes i Git». A data product's aggregate
contract (every member table in one document) is never written to this repo;
download it from the data product page in Specly. It has the same root `id`
and the same `speclyId` custom property as the `.odps.yaml`.

```yaml
apiVersion: v1.1.0
kind: DataProduct
id: Sales
name: Sales
status: Active
outputPorts:
  - name: Sales
customProperties:
  - property: speclyId
    value: 7c2e4a6b-9d1f-4e83-a5b7-0c9e2d4f6a18
  - property: tables
    value:
      - customer
      - orders
```

## More editing rules
- References (`physicalType`, `status`, flag names in `tags`, `tableType`,
  `transformSourceObjects`, `upstreamTables`, …) are matched by name
  against `Config/*.json` or the other contracts. Add to the registry first if
  the value is new.
- Give diagram placements their `tableUuid` next to the name; the uuid wins
  when present.
- A table's `quality` (and a column's) holds its data-quality rules in ODCS
  `quality[]` vocabulary; edit them here or in Specly, both round-trip.
  Keep a rule's `id`: renamed with its `id` kept, it stays the same rule. A
  new rule may omit it; the import then matches it by where it sits and by
  its `name`.
- A table-type field's value goes where its mapping sends it: an ODCS key an
  admin mapped it to (`businessName`, `physicalName`, `tags`, `domain`,
  …), or a `customProperties` entry named by the field definition's
  `odcsPropertyName` in `Config/metadata_field_definitions.json` — its
  `key` when that is unset, never its display name. In this project that is
  `Datoeffektiv på` (`datoeffektiv_pa`) as `datoeffektivPa`. A field whose
  mapping is invalid is not written, and its contract is held back. "Table
  type fields" under "This project" lists where each of this project's
  fields goes.
- A table object's `deprecated` is yours: Specly doesn't write it (no table
  status marks a table deprecated), and an export keeps what the file says.

## This project

**Folder layout:**
- All paths below are rooted under `specly/`.
- Diagrams: `Diagrams/<name>.json`
- Table contracts: `Tables/<type>/<name>.odcs.yaml` (grouped into a subfolder per table type: the type's name, or its own Git folder when it sets one) — Open Data Contract Standard documents, this project's table and data product definitions on import.
- Data product documents: `DataProducts/<name>.odps.yaml` (Open Data Product Standard).
- Relations: only in the `from` table's contract — a single-column key as `to: <table>.<column>` on its `from` property, a composite one as a schema-level `relationships` entry with `from`/`to` lists of `<table>.<column>`; each with `id` = the relation's uuid (`comment`/`sourceCardinality`/`targetCardinality` as `customProperties`). There is no `relations.json`; a diagram keeps only each relation's route, under `relationBreakpoints`, keyed by that `id`.
- Config: `Config/*.json`
- Entities sharing a name get a `.<uuid8>` filename suffix for disambiguation; identity is the `uuid` field inside the file either way.

**Table naming:**
- `database`: not used
- `schema`: not used

**ODCS settings:**
- `columnBusinessNameSource`: `downstreamName` — a column's `businessName`
  is its downstream name; the `downstreamName` built-in writes nothing else.
- `referenceStyle`: `namedRefs` — tables, columns, relations and quality
  rules carry their uuid `id`; a relation is written once and its reference
  is `<table>.<column>`.
- `quoteAllStrings`: `false` — a string value is quoted only where YAML
  needs it, as in the examples.
- `tableTypeFields`: `true`, `tablePhysicalTypeDefault`: `table` — a table
  object carries `logicalType: object` and a `physicalType`, `table` unless
  a field mapped to it sets one.
- `deprecatedTableStatusUuids`: none — Specly doesn't write a table
  object's `deprecated`.
- `primaryKeyPosition`: `false` — a key column carries no position; the
  key's column order is the order in `properties`.
- `primaryKeyRequired`: `true` — every key column is written
  `required: true`; next to `primaryKey: true` the import reads it as part
  of the key, not as the required flag.

**Built-in fields** (Specly's own fields, mapped under Admin → ODCS → «Specly-felt»; where each is written on export and read back from on import):
- `owner`: the data product's `team.name`
- `dataProductStatus`: the data product's `status` (the status's
  `odcsStatus`, else its name), plus the data product's `status` custom
  property only when that value can't lead back to exactly this status
- `tableType`: the table object's `tableType` custom property
- `tableStatus`: the contract's root `status` (the status's `odcsStatus`,
  else its name), plus the table object's `status` custom property only when
  that value can't lead back to exactly this status
- `sourceSystem`: the table object's `sourceSystem` custom property
- `databaseName`: the table object's `databaseName` custom property
- `schemaName`: the table object's `schemaName` custom property
- `excludeFromSorting`: the table object's `excludeFromSorting` custom
  property
- `upstreamTables`: the table object's `upstreamTables` custom property
- `businessKey`: the property's `businessKey` custom property
- `columnStatus`: the property's `status` custom property
- `downstreamName`: the property's `businessName`
  (`columnBusinessNameSource: downstreamName`)
- `developerNote`: the property's `transformDescription`
- `upstreamColumns`: the property's `transformSourceObjects`; a column
  marked as having broken the rename rule keeps its entries in the
  `upstreamColumns` custom property (see "Column lineage")

**Table type fields** (where each field is written on export and read back from on import):
- `raw`
  - column field `Beskrivelse` (`description`): built-in, keep it; written
    as the property's `description`
  - column field `Utviklernotat` (`developerNote`): built-in, keep it;
    written as the property's `transformDescription`
- `bronze`
  - column field `Beskrivelse` (`description`): built-in, keep it; written
    as the property's `description`
  - column field `Utviklernotat` (`developerNote`): built-in, keep it;
    written as the property's `transformDescription`
  - column field `Rensing` (`rensing`): the property's `rensing` custom
    property
- `sølv`
  - table field `Radfilter` (`radfilter`): the table object's `radfilter`
    custom property
  - column field `Beskrivelse` (`description`): built-in, keep it; written
    as the property's `description`
  - column field `Utviklernotat` (`developerNote`): built-in, keep it;
    written as the property's `transformDescription`
  - column field `Beregning` (`beregning`): the property's `transformLogic`
- `gull dimensjon`
  - table field `Historikk` (`historikk`): the table object's `historikk`
    custom property
  - column field `Beskrivelse` (`description`): built-in, keep it; written
    as the property's `description`
  - column field `Utviklernotat` (`developerNote`): built-in, keep it;
    written as the property's `transformDescription`
- `gull fakta`
  - table field `Radfilter` (`radfilter`): the table object's `radfilter`
    custom property
  - column field `Beskrivelse` (`description`): built-in, keep it; written
    as the property's `description`
  - column field `Utviklernotat` (`developerNote`): built-in, keep it;
    written as the property's `transformDescription`
  - column field `Beregning` (`beregning`): the property's `transformLogic`
  - column field `Datoeffektiv på` (`datoeffektiv_pa`): the property's
    `datoeffektivPa` custom property

**`description` and `developerNote` are built-in column fields, not custom
ones.** Specly needs both in every table type's column fields: without them
the column's description and developer note disappear from the Specly UI, so
never delete them. Their own `odcsTarget` and `odcsPropertyName` in the
field definitions are not used. A column's description is always written as
the property's `description`. Its developer note is written where the
`developerNote` built-in says (see "Built-in fields": the property's
`transformDescription`). Neither is ever written as a custom field value,
and neither holds a contract back.

**Enforced rules** (from `.specly/lint.json` — `rules` violations block a push, `enums` violations are reported but do not block):
- `ambiguousNameReference`: a table, diagram or data product name isn't required to be unique — but a bare-name reference (a relation endpoint, diagram placement, lineage source, data-product member, concept column link) that matches more than one entity is rejected. Include the referenced entity's `*Uuid`/`uuid` field (written next to the name on export) to disambiguate.
- `lineageTargetMustExist`: true
- `rejectFabricatedUuids`: true
- Enum membership (dataTypes, flags, tableStatuses, columnStatuses, diagramStatuses, dataProductStatuses) is checked against `Config/*.json` and reported, but never blocks a push. It is reported in «Fra Git» (an unknown data type becomes a row that asks for a type to pick, an unknown status is a problem to fix in Git) and in the warnings of the Git import preview.
- Admin-only: a create, rename, or (mirror-mode) delete in `Config/business_concept_rules.json`, `Config/column_sorting_rules.json`, `Config/column_statuses.json`, `Config/data_product_statuses.json`, `Config/datatypes.json`, `Config/diagram_statuses.json`, `Config/flag_rules.json`, `Config/flags.json`, `Config/metadata_field_definitions.json`, `Config/odcs.json`, `Config/person_roles.json`, `Config/relation_rules.json`, `Config/table_naming.json`, `Config/table_statuses.json`, `Config/table_types.json` is rejected with 403 `admin_settings_change` unless the account applying the push/import has the project's `Admin` role.

## Diagrams, concepts, registries and your own files
1. A diagram's `folder` is a `/`-separated path, root first (escape a
   literal `/` in a folder name as `\/`); folders are created on push if
   they don't already exist, not matched against a registry.
2. Admin settings: `Config/datatypes.json`, `flags.json`,
   `table_statuses.json`, `column_statuses.json`, `diagram_statuses.json`,
   `data_product_statuses.json`, `table_types.json` and
   `metadata_field_definitions.json` are registries, each validated
   element-by-element against its own schema in `.specly/schemas/`
   (`datatype`/`flag`/`status`/`tabletype`/`metadata_field_definition`
   — `status` is shared by all four `*_statuses.json` files).
   `relation_rules.json`, `flag_rules.json` and `column_sorting_rules.json`
   have no schema here — edit those in Specly, not the repo. A new registry
   entry may carry a `uuid` v4 you generate, which Specly keeps; without
   one the import gives it a uuid derived from its name (see "Recipe: change a
   registry entry"). A registry file that does not
   exist yet (Specly writes one only when an entry of it is exported) can be
   created as a JSON list of such entries. A table type wires
   in a metadata field definition via `columnFieldDefUuids`/
   `metadataFieldDefUuids`, each element either an existing definition's
   `uuid` or (for one added in the same push) its `key`. Next to each uuid
   reference a table type carries its readable name — `columnFields`/
   `tableFields` (the definitions' `key`s), `columnTemplates[].dataType`
   (the datatype's name) and `columnTemplates[].flags` (next to
   `flagUuids`, the flags' names); likewise a flag rule's `flag` next to its
   `flagUuid`, and a column sorting rule's `dataType` next to its
   `datatypeUuid` (the flag's / datatype's name). The uuid decides; a
   name that disagrees with its uuid rejects the import, so change both,
   or remove the name. A name with
   no uuid next to it is resolved by that name. Pushing a change to
   one of these registries may require an admin to apply the import in
   Specly rather than a regular member — a per-project toggle, same as the
   other project policies `.specly/lint.json` publishes.
3. Branch settings: `Config/odcs.json` (`columnBusinessNameSource`:
   `field`/`downstreamName`, `quoteAllStrings`, `referenceStyle`:
   `namedRefs`/`shorthand`, `tableTypeFields`: whether each table object carries
   `logicalType: object` and a `physicalType`, `tablePhysicalTypeDefault`:
   that `physicalType` when no mapped field sets it,
   `deprecatedTableStatusUuids`: the table statuses whose tables get
   `deprecated: true` — empty leaves a contract's own `deprecated` alone,
   `primaryKeyPosition`, `primaryKeyRequired`),
   `Config/table_naming.json` (`database`/`schema`:
   `off`/`optional`/`required`) and the folder and format fields of
   `.specly.json` are this branch's settings. A change to them is reviewed
   like a registry change, with the same admin rule, and applies to this
   branch only. A key or file left out changes nothing; `rootFolder`,
   `adminOnlyConfigImport` and `protectedBranches` are never read from Git.
   After such a change this guide file itself, and `.specly/format.json`,
   are stale until Specly's next export, which brings its helper files up to
   date: leave them alone (see "Recipe: change a format setting from Git").
4. A metadata field with `odcsTarget: customProperties` — or, for a table
   or column field, no `odcsTarget` — is written in a contract as its own
   `customProperties` entry: `property` is its
   `odcsPropertyName`, else its key in camelCase; the entry has no `id`. How
   its value is written depends on the field's `fieldType` (see "Metadata
   field types" above for a contracts repo). A structured property in
   `Config/odcs.json` (`customProperties[]`: a tree of `nodes` whose leaves
   name a field or flag by `source.uuid`) is written in place of those
   entries. A field one of its leaves names must have
   `odcsTarget: customProperties` and `odcsPropertyName` equal to the
   property's `name`; otherwise the field is written somewhere else too and
   the mapping is rejected as `sourceMappedTwice`. The import reads an empty
   `odcsTarget` as `customProperties`, so a field added for a tree needs that
   `odcsPropertyName`. A table or data product field with
   `odcsTarget: slaProperties` is an `slaProperties` entry whose `property`
   is its key in camelCase (the key itself reads too).
5. Specly only creates, updates and deletes files listed in
   `.specly/files.json`. Put your own files anywhere, including inside these
   folders (a dbt model next to a table's file) — Specly never overwrites or
   deletes a file it didn't write itself. A file you add that Specly takes in
   (a new contract for a table) is Specly's from then on: the next export
   lists it in `.specly/files.json` without rewriting it, and later edits or a
   delete in Specly update or remove it.

**Recipe: change a registry entry**
- New entry: add it to the registry file. It may carry a `uuid` v4 you
  generate; Specly keeps it (the `rejectFabricatedUuids` rule checks only
  references to tables, columns and diagrams). Prefer to give one: an entry
  without `uuid` is given one derived from its name, and a branch Specly never
  exports to (a protected branch such as `main`) gets it written back only when
  another branch's export reaches the file, so until then a rename of that
  entry is read as a delete plus a new entry.
- Rename: keep the entry's `uuid`, change `name`, and change every use by name
  in the same push: each column's `physicalType` (data type), `tags` (flag),
  `status` (table, column, diagram or data product status), `tableType`, and
  every field value naming a person or source system. A use left on the old
  name is a name Git's registry no longer holds: for a table type, source
  system, flag, status or person it reads as no value (the table or column
  loses it, and nothing is listed); for a data type it is «Trenger type», a
  row that asks for a type to pick.
- Move a value to another registry (a table status to a column status, say):
  that is a delete in the one file and a NEW entry in the other, with a new
  `uuid`; the uses change by name, as for a rename.
- Delete: remove the entry. Git is the truth for registry values: «Hent inn»
  removes the value in Specly and everything that used it loses it (a table its
  type, status or source system; a column its status or flags; a diagram or
  data product its status; a person or source system its uses in field
  values), and «Fra Git» says beforehand how many tables, columns and the like
  lose it. Remove or replace the uses in the same push. A column still naming a
  deleted data type is «Trenger type» in «Fra Git».
- `odcsStatus` on a status entry is the ODCS lifecycle value (`active`, …) a
  contract's `status` is read as.

**Recipe: edit a diagram**
A diagram is `Diagrams/<name>.json`; its placements are the `tables` list:

```json
{
  "uuid": "6f1b9a4e-2d7c-4b83-9a05-3c8e1d5f7a20",
  "name": "Sales overview",
  "description": "",
  "folder": "Sales/2026",
  "tables": [
    { "table": "customer", "tableUuid": "3f6c2a1e-8b4d-4c7a-9e21-5d0b7f3a6c11", "x": 120, "y": 80 }
  ]
}
```

- A placement needs `table`, `x` and `y` (numbers, rounded to whole numbers);
  `tableUuid` is optional and wins over `table` when present. A placement
  names a table Git has: one it does not have is left out and listed under
  «Må rettes i Git».
- Add or remove a table: add or remove its entry in `tables`. Removing a
  placement keeps the table.
- New diagram: a new file in the diagrams folder, named like a table's file (the
  name is not read; Specly writes `<name>.json`), with a `uuid` v4 you
  generate (the import rejects the file without one), `name`, `description`
  (may be empty) and `tables`. `folder` is optional (see item 1 above);
  `status` (a name from `Config/diagram_statuses.json`) and `sourceSystems` are
  too.
- Delete a diagram: delete its file; the tables stay.
- Before you delete a table, remove its placements in the same push.

**Recipe: change a format setting from Git**
- Edit the key in `Config/odcs.json` (or `Config/table_naming.json`) and push;
  leave `.specly/format.json` and this guide file alone. «Fra Git» lists the
  settings change on its own, first, and says how many tables or columns lose a
  value because of it; «Hent inn» takes it in. It is reviewed like a registry
  change (an admin may be needed) and applies to this branch only.
- When the change renames or moves the `customProperties` entry a built-in or
  field is written under, rewrite every contract that carries the old name in
  the same push. A contract left on the old name is read under the new
  setting, where that property is no longer taken: the value goes, and «Fra
  Git» counts it among what the settings change removes.
- Specly writes its helper files again in its next export; until then this
  guide file is stale.

## Built-in column fields: `description` and `developerNote`
`Config/metadata_field_definitions.json` holds two entries with `key`
`description` (label «Description») and `developerNote` (label «Developer
Note»), `entityTypes: ["column"]`. They are Specly's own column fields, not
custom ones, and they look like custom fields only because they share the
file. Never delete them, and keep them in every table type's `columnFields`:
without them a column's description and developer note disappear from the
Specly UI. Their `odcsTarget` and `odcsPropertyName` are not used; a
column's description is always its `description`, and its developer note
goes where the `developerNote` built-in says. Neither holds a contract back.
A custom field cannot take either key.

## Key order
Keys are matched by name, so a file whose keys are in another order than
Specly writes them means the same: a file that differs only in key order is
not a change and is not rewritten. When a contract, data product or concept
file changes, the export changes those values in place and keeps your key
order; only a file new from Specly's side gets its fixed order («Nytt
filformat» leaves a file that equals Specly's as values alone and keeps your
order in one it rewrites; a file it does rewrite loses its comments and comes
out with LF line endings, and a switch to unquoted strings leaves a concept
file's quotes as they are). A `Config/*.json` registry file is
different: an export that takes a change to one of its entries writes the
whole file again, in Specly's JSON layout (two-space indent, no final
newline), entries sorted as below. In that file:
- an entry whose field changed in Specly is your entry with just that key
  set to Specly's value: your key order and your other keys stay (a key you
  lack goes last);
- every other entry Specly holds under the same `uuid` and that says the
  same in the keys Specly writes is written as Specly writes it: its key
  order, and keys Specly does not write (a key you added by hand) are
  dropped;
- an entry you added without `uuid` stays as you wrote it, still without
  `uuid`, and sorts as if its uuid were empty;
- an entry that differs from Specly's in a change this export does not
  take, and an entry only Git has, stay as Git has them.

So a hand-edited key order, or a key of your own, in an entry Specly
holds survives only until the next export that changes anything in that
file. `check` does not report this. In `Config/*.json` an entry Specly
writes starts with `uuid`, then its keys in the order of its registry (for a metadata field: `label`, `entityTypes`, `key`,
`fieldType`, `dropdownOptions`, `isMultiSelect`, `sortOrder`, `optionColors`,
`isRequired`, `glossaryLinkable`, `isSharedDropdown`, `odcsTarget`,
`odcsPropertyName`, `suggestible`, `description`, then the optional
governance keys); the entries are sorted by `order`/`sortOrder`/`priority`,
then `uuid`.

## Workflow
    git commit && git push   # to any branch

Each Git branch has a Specly branch of the same name (a new Git branch gets
one). After your push, that Specly branch shows the commit as pending
changes. Someone opens «Fra Git» there and clicks «Hent inn»: everything that
doesn't collide with an edit made in Specly is taken, removals included
(nothing is ticked or unticked item by item). Where Specly changed the same
field, the reviewer chooses which side to keep — applying is a human click in
Specly, never
automatic. An export after that commits only what changed in Specly since
(an edit made there, links after «Bruk reglene», an automatic rename) into
your files, in their own layout; it adds no `id` to a table, column or
relation, and does not reorder keys. Pull before you push again. Edits made
in Specly reach the branch the same way, as an export commit.

On a protected branch (one of the `protectedBranches` patterns of
`.specly/lint.json`, typically `main`) Specly takes changes in but never commits back. Ids Specly assigns
there (a new relation's `id`, a registry `uuid`) reach Git with the next export
from another branch, so until then those files lack them.

## Deletes

Deleting a table's `.odcs.yaml` deletes the table, and removing a property from its `properties` deletes the column — but only once someone applies it in Specly:
- «Fra Git» lists each removed table and column as a removal, and «Hent inn» takes it with everything else that doesn't collide with an edit made in Specly; there is no per-item untick. A table or column added in Specly since the last sync is never listed as a removal.
- A full import in mirror mode soft-deletes every live table and column the contracts no longer contain.
- A table or column removal is refused while a relation still points at it (one another contract's `relationships` states, or one made in Specly and never exported), and a diagram placement or data product member that names a deleted table is listed under «Må rettes i Git»: remove those references, and the `transformSourceObjects` references to it, in the same push.
- Emptying a folder (e.g. every contract under the tables folder) soft-deletes **every live entity of that kind** — this requires an explicit force flag; it is not blocked outright.
- Renaming or moving a contract file is safe: `schema[0].id` identifies the table, not its path. Specly never moves it back; it moves a file only when it exports a change of its table's name or table type (see "Recipe: rename or move a contract file").
- If you're not sure whether an apply will run in mirror mode, treat every file or property removal as a delete.

## Don'ts
- Don't write to `.specly.json` or anything under `.specly/` (`format.json`,
  `files.json`, `lint.json`, `root-files.json`, `schemas/`). Specly maintains them.
- Don't invent a uuid for an entity that already exists, and don't change one
  — generate a uuid v4 only for an entity you are adding.
- Don't reference data types / flags / statuses that aren't in `Config/`.

For schema details see `.specly/schemas/README.md`.
