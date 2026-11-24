#!/usr/bin/env python3
"""Bygger kursrepoet (malrepoet deltakerne kopierer med «Use this template») fra dette utviklingsrepoet.

  python3 tools/lag_kursrepo.py ../specly-toppfart

Målmappen tømmes (unntatt .git) og fylles med:
  - kurset: moduler/, kilder/, notebooks/, maler/, databricks/, tools/, fasit/, .startpunkter/ og kommandoene
  - docs/: bare det modultekstene viser til (design, fasit, kjente Specly-feil), notatene til kursholder og introsiden
  - specly/: startpunktet for modul 2 (prosjektoppsettet, ingen tabeller), uten projectId i .specly.json, slik at
    deltakerens eget Specly-prosjekt tar repoet som det er
  - README.md og .gitignore for deltakeren

Ikke med: rapporter, statusnotater og klikkgjennomganger i docs/, CLAUDE.md, tester/, og den genererte koden for
tabellene (den lages av ./generer eller notebooken når deltakeren har tabeller).
Skriptet committer ikke. Se etter i målmappen, og commit og push selv.
"""
import json
import os
import shutil
import sys

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROT, "tools"))
from kursmoduler import startpunkt_mappe  # noqa: E402

MED = [".startpunkter", "databricks", "databricks.yml", "fasit", "generer", "kjor", "kurs", "kilder", "maler",
       "moduler", "notebooks", "tools"]
DOCS = ["design.md", "fasit.md", "kursholder.md", "specly-feil.md", "kurs-intro.html"]
IKKE = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc", ".pytest_cache", ".ruff_cache")

README = """# Specly-kurset: Toppfart Sport

Et opplæringskurs i datamodellering med Specly og Databricks. Du modellerer en oppdiktet sportskjede, Toppfart Sport
AS, fra rådata til stjerner i gull. Koden som bygger tabellene i Databricks, genereres fra modellen med Data Contract
CLI og Jinja-maler.

**Hva er kurset?** Se introsiden [docs/kurs-intro.html](docs/kurs-intro.html). GitHub viser HTML som kildekode: last
ned filen og åpne den i nettleseren.

## Slik starter du
1. Trykk «Use this template» → «Create a new repository» øverst på denne siden. Velg din egen GitHub-konto som eier,
   og la repoet være privat.
2. Følg [modul 0](moduler/M0.md). Den kobler repoet ditt til ditt eget Specly-prosjekt og din egen
   Databricks-arbeidsflate.

## Hva du trenger
- En GitHub-konto der du kan installere apper på dine egne repoer.
- En invitasjon til Specly fra kursholderen. Prosjektet lager du selv i modul 0.
- En Databricks-arbeidsflate. Databricks Free Edition holder.
- Et personlig tilgangstoken i Databricks til importen i modul 2, i begge spor. Modul 2 viser hvordan du lager det, og
  har en omvei hvis du ikke kan.
- Nettlesersporet: bare nettleser. Terminalsporet: `git`, `gh`, `uv`, Databricks CLI og Data Contract CLI
  (`uv tool install datacontract-cli==1.2.10`). Se modul 0. Velg ett spor og hold deg til det: de to sporene kan ikke
  dele et skjema i Databricks.

## Modulene
| # | Modul | Fil |
|---|---|---|
| 0 | Oppsett | [M0](moduler/M0.md) |
| 1 | Prosjektoppsett (valgfri, for admin) | [M1](moduler/M1.md) |
| 2 | Raw fra kilden | [M2](moduler/M2.md) |
| 3 | Bronze | [M3](moduler/M3.md) |
| 4 | Sølv | [M4](moduler/M4.md) |
| 5 | Første stjerne | [M5](moduler/M5.md) |
| 6 | Ny kilde: nettbutikken | [M6](moduler/M6.md) |
| 7 | Kunden og historikk | [M7](moduler/M7.md) |
| 8 | Dokumentasjon og styring | [M8](moduler/M8.md) |
| 9 | Forretningsbegreper | [M9](moduler/M9.md) |
| 10 | Dataprodukt | [M10](moduler/M10.md) |
| 11 | Lagerbeholdning | [M11](moduler/M11.md) |

Modul 11 er den siste, og slutter med en oppsummering av hva du har bygget, og hva kurset har laget i Databricks.

Hver modul har en løsning (`moduler/M<n>_losning.md`). Med `./kurs til M<n>` (eller notebooken `kurs_til`) kan du
starte på hvilken som helst modul fra og med modul 2. Se [moduler/start.md](moduler/start.md).
"""

GITIGNORE = """data/
__pycache__/
.pytest_cache/
.DS_Store
.databricks/
spark-warehouse/
"""


# Linjene Databricks selv skriver øverst i en notebookfil når den kjøres på serverless. Står de i filene fra før (og
# filen slutter uten linjeskift), endrer ikke Databricks filen ved kjøring, og «Pull» i Git-mappen gir ikke
# flettekonflikt når kursholder retter en notebook underveis. Notebookene kopieres byte for byte. Skriptet sier fra
# hvis en av dem mangler hodet.
NOTEBOOKHODE = ('# Databricks notebook source\n# /// script\n# [tool.databricks.environment]\n'
                '# environment_version = "6"\n# ///\n')


def notebooker_uten_hode(mappe):
    """Notebookfilene i mappen som ikke begynner med NOTEBOOKHODE, eller som slutter med linjeskift."""
    feil = []
    for navn in sorted(os.listdir(mappe)):
        if navn.endswith(".py"):
            tekst = open(os.path.join(mappe, navn), encoding="utf-8").read()
            if not tekst.startswith(NOTEBOOKHODE) or tekst.endswith("\n"):
                feil.append(navn)
    return feil


def tom(mappe):
    os.makedirs(mappe, exist_ok=True)
    for navn in os.listdir(mappe):
        if navn == ".git":
            continue
        sti = os.path.join(mappe, navn)
        shutil.rmtree(sti) if os.path.isdir(sti) and not os.path.islink(sti) else os.remove(sti)


def kopier(fra, til):
    if os.path.isdir(fra):
        shutil.copytree(fra, til, ignore=IKKE)
    else:
        shutil.copy2(fra, til)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    mal = os.path.abspath(sys.argv[1])
    if mal == ROT or mal.startswith(ROT + os.sep):
        sys.exit("Målmappen må ligge utenfor utviklingsrepoet.")
    tom(mal)
    for navn in MED:
        kopier(os.path.join(ROT, navn), os.path.join(mal, navn))
    os.makedirs(os.path.join(mal, "docs"))
    for navn in DOCS:
        kopier(os.path.join(ROT, "docs", navn), os.path.join(mal, "docs", navn))

    specly = os.path.join(mal, "specly")
    shutil.copytree(startpunkt_mappe("start", 2), specly)
    manifest = os.path.join(specly, ".specly.json")
    m = json.load(open(manifest))
    m.pop("projectId", None)
    with open(manifest, "w") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)

    feil = os.path.join(mal, "docs", "specly-feil.md")
    tekst = open(feil).read().replace("# Kjente feil og friksjon i Specly, til Steffen", "# Kjente feil og friksjon i Specly", 1)
    with open(feil, "w") as f:
        f.write(tekst)

    tabeller = os.path.join(mal, "databricks", "pyspark", "tabeller")
    shutil.rmtree(tabeller, ignore_errors=True)
    os.makedirs(tabeller)
    # Git tar ikke vare på en tom mappe. Generatoren (tools/generer.py) fjerner .gitkeep første gang den skriver koden,
    # fordi pipelinen bare tåler .py og .sql i mappen.
    open(os.path.join(tabeller, ".gitkeep"), "w").close()

    with open(os.path.join(mal, "README.md"), "w") as f:
        f.write(README)
    with open(os.path.join(mal, ".gitignore"), "w") as f:
        f.write(GITIGNORE)
    uten = notebooker_uten_hode(os.path.join(mal, "notebooks"))
    if uten:
        print("NB: disse notebookene mangler hodelinjene Databricks skriver (eller slutter med linjeskift), og vil stå "
              f"som endret i Git-mappen etter første kjøring: {', '.join(uten)}. Se NOTEBOOKHODE i tools/lag_kursrepo.py.")
    print(f"Kursrepoet er bygget i {mal}. Se etter, og commit og push selv.")


if __name__ == "__main__":
    main()
