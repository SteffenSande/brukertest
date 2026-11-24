# Specly Database Schema

This repository contains an export of your database schema from Specly.

## Structure

- `specly/Config/` - Global configuration (data types, flags, statuses, rules)
- `specly/Diagrams/` - Diagram configurations with table positions and relation routes
- `specly/Tables/` - Table definitions as Open Data Contract Standard (ODCS v3.2.0) documents (`<name>.odcs.yaml`). Read back on import.
  Each relation is edited in its `from` table's contract (`relationships`, `id` = the relation's uuid); a diagram file keeps only each relation's route there (`relationBreakpoints`).
- `specly/DataProducts/` - Data product definitions as Open Data Product Standard (ODPS v1.1.0) documents (`<name>.odps.yaml`). Read back on import.

## About Specly

Specly is a powerful database schema visualization and management tool.
Visit [Specly](https://specly.no) to learn more.
