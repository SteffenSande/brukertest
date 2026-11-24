# Specly JSON Schemas

This directory holds JSON Schemas generated from Specly's TypeScript
entity types. They are the source of truth for entity file shape.

- `diagram.schema.json`      — diagrams/*.json
- `datatype.schema.json`     — each element of Config/datatypes.json
- `flag.schema.json`         — each element of Config/flags.json
- `status.schema.json`       — each element of Config/table_statuses.json, column_statuses.json, diagram_statuses.json, data_product_statuses.json
- `tabletype.schema.json`    — each element of Config/table_types.json
- `metadata_field_definition.schema.json` — each element of Config/metadata_field_definitions.json

`Config/relation_rules.json`, `flag_rules.json` and `column_sorting_rules.json`
have no schema here — they're edited in Specly, not the repo.

Cross-entity reference rules (lineage targets, dataType/status/flag name
resolution, ambiguous-name-reference rejection) live in `../lint.json` and
are checked by Specly when it reads your push.

Do not hand-edit these files. They are regenerated on every Specly export.

Specly only touches files listed in `.specly/files.json`; put your own files
anywhere, including inside these folders — a foreign file next to a Specly
export is never read, overwritten, or deleted.
