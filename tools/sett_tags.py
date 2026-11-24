#!/usr/bin/env python3
"""Tags i Unity Catalog etter kontraktene, etter at pipelinen er ferdig. Siste steg i ./kjor (modul 8).

  uv run --no-project --with pyyaml python3 tools/sett_tags.py
  uv run --no-project --with pyyaml python3 tools/sett_tags.py --vis      bare vis setningene, kjør ingenting

Taggene står i databricks/pyspark/plattform/tags_data.py (./generer lager den fra kontraktene). Selve arbeidet gjør
plattform/tags.py, den samme koden notebookene kjører. Her går SQL-en gjennom SQL warehouse i arbeidsflaten, med
Databricks CLI-profilen (som ./kurs sjekk). Ingen token leses eller skrives ut.
Miljø: DATABRICKS_PROFILE (standard kurs), KATALOG (workspace), SKJEMA (toppfart).
"""
import importlib
import os
import sys

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROT, "tools"))
sys.path.insert(0, os.path.join(ROT, "databricks", "pyspark"))


def main():
    profil = os.environ.get("DATABRICKS_PROFILE", "kurs")
    katalog = os.environ.get("KATALOG", "workspace")
    skjema = os.environ.get("SKJEMA", "toppfart")
    tags = importlib.import_module("plattform.tags")
    data = importlib.import_module("plattform.tags_data")
    if "--vis" in sys.argv:
        for setning in tags.setninger(katalog, skjema, data.TAGS, data.EIDE_NOKLER):
            print(setning)
        return
    from test_fasit_lokalt import databricks_sql
    antall = tags.sett_tags(databricks_sql(profil, katalog, skjema), katalog, skjema, data.TAGS, data.EIDE_NOKLER)
    print(f"       {antall} setninger for tags i {katalog}.{skjema}" + ("" if antall else " (alt stod riktig fra før)"))


if __name__ == "__main__":
    main()
