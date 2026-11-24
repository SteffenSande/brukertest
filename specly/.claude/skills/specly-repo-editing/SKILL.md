---
name: specly-repo-editing
description: Editing rules and push workflow for this Specly export. Use before editing Tables/, Diagrams/, DataProducts/ or Config/ files, any .odcs.yaml data contract or .odps.yaml data product, and before pushing to Git.
---

# Editing this Specly export

This repo is an export of a Specly project. Read `AGENTS.md` in the export's
root folder before you edit anything: it holds the editing rules for this
project's format (JSON files or `.odcs.yaml` data contracts), with a recipe
for each kind of change, and this project's actual folder layout.

After you push, open the merge review on the Specly branch of the same name
and check it: an existing table or column must never show as new. If one
does, fix its `id` and push again.
