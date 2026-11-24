# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Kursoppsett (nettlesersporet)
# MAGIC
# MAGIC Det samme som `./kurs oppsett` i terminalsporet:
# MAGIC
# MAGIC 1. Lager skjemaet og landingsvolumet i din Databricks.
# MAGIC 2. Lager kildefilene (oppdiktede, alltid de samme) og legger dem i landingsvolumet.
# MAGIC 3. Lager kildetabellene du henter inn i Specly i modul 2 (steg 1): ett skjema per kilde
# MAGIC    (`<skjema>_kilde_kassio` osv.) med ett view per tabell over filene.
# MAGIC
# MAGIC Kjør notebooken fra repoet ditt som Git-mappe i Databricks, på serverless. Ingen token trengs.
# MAGIC Dette finnes bare fordi det er et kurs: i et ekte prosjekt finnes kildene fra før.
# MAGIC
# MAGIC **Velg ett spor.** Gjør du oppsettet her, gjør du resten av kurset med notebookene. `./kurs` og `./kjor` i
# MAGIC terminalsporet vil lage skjemaet selv, og stopper når det finnes fra før (modul 0, «Velg spor»).
# MAGIC
# MAGIC **Feltene (parametere):** Første gang du åpner notebooken, og etter hver «Pull» i Git-mappen, har den ingen
# MAGIC felt («No parameters»). Trykk «Run all»: den kjører med standardverdiene (katalog `workspace`, skjema `toppfart` og volum `landing`), og etterpå
# MAGIC ligger feltene i sidepanelet «Parameters» (knappen «Show parameters»). Skjemaet `toppfart` er riktig for de fleste.
# MAGIC
# MAGIC **Vil du ha et annet skjema enn `toppfart`?** Da setter du skjemaet før du trykker «Run all»:
# MAGIC 1. Kjør bare cellen «Feltene» rett under denne: hold pekeren over cellen og trykk ▶ øverst til venstre i den.
# MAGIC    Cellen lager feltene og gjør ikke noe annet.
# MAGIC 2. Skriv skjemanavnet i feltet «Skjema» i sidepanelet «Parameters», og trykk Enter.
# MAGIC 3. Vent til knappen «Run all» er tilbake, og trykk «Run all».
# MAGIC
# MAGIC **Når du har endret et felt:** Databricks kjører cellen som leser feltene på nytt av seg selv. Mens den går, står det
# MAGIC «Interrupt» der «Run all» pleier å stå. Vent til «Run all» er tilbake før du trykker. Trykker du for tidlig, blir
# MAGIC kjøringen avbrutt («Cancelled») og ingenting annet kjører. Utskriftene du ser, er da fra forrige kjøring.
# MAGIC
# MAGIC Her er rekkefølgen ekstra viktig: trykker du «Run all» først, lager notebooken skjemaet `toppfart` og seks
# MAGIC kildeskjemaer (`toppfart_kilde_…`) før du har fått valgt. Bruk samme skjema i de andre notebookene etterpå.

# COMMAND ----------

# Feltene. Cellen lager bare feltene i sidepanelet «Parameters» og endrer ingenting. Den står for seg selv og først, så
# du kan kjøre bare den (▶) og sette feltene før resten av notebooken kjører. Finnes feltene fra før, beholder de verdien.
dbutils.widgets.text("katalog", "workspace", "Katalog")
dbutils.widgets.text("skjema", "toppfart", "Skjema")
dbutils.widgets.text("volum", "landing", "Volum")

# COMMAND ----------

KATALOG = dbutils.widgets.get("katalog")
SKJEMA = dbutils.widgets.get("skjema")
VOLUM = dbutils.widgets.get("volum")

import os
import shutil
import subprocess
import sys
import tempfile

# Notebooken ligger i notebooks/ i repoet; verktøyene i tools/.
ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
from kildetabeller import KILDER, kildeskjema, sql_for_kildene

print(f"Oppsett i {KATALOG}.{SKJEMA}, volum {VOLUM}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Skjema og landingsvolum
# MAGIC Terminalsporet gjør dette med `databricks bundle deploy` (databricks.yml). Her med SQL.
# MAGIC Pipelinen lages ikke her: den kommer med genereringen og kjøringen.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {KATALOG}.{SKJEMA} COMMENT 'Specly-kurset (Toppfart Sport AS). Tabellene lages av pipelinen, fra Specly-kontraktene.'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {KATALOG}.{SKJEMA}.{VOLUM} COMMENT 'Filene slik kildene leverer dem.'")
print(f"Skjema {KATALOG}.{SKJEMA} og volum /Volumes/{KATALOG}/{SKJEMA}/{VOLUM} finnes.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Kildefilene
# MAGIC `data/` ligger ikke i Git. Filene lages derfor her med den samme generatoren som i terminalsporet
# MAGIC (`tools/lag_data.py`, deterministisk), og kopieres til volumet.

# COMMAND ----------

landing = f"/Volumes/{KATALOG}/{SKJEMA}/{VOLUM}"
with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run([sys.executable, os.path.join(ROT, "tools", "lag_data.py"), "--rot", tmp], capture_output=True, text=True)
    print(r.stdout[-2000:], r.stderr[-2000:])
    assert r.returncode == 0, "Datageneratoren feilet."
    lokalt = os.path.join(tmp, "data", "landing")
    antall = 0
    for mappe, _, filer in os.walk(lokalt):
        for f in filer:
            til = os.path.join(landing, os.path.relpath(os.path.join(mappe, f), lokalt))
            os.makedirs(os.path.dirname(til), exist_ok=True)
            shutil.copyfile(os.path.join(mappe, f), til)
            antall += 1
print(f"{antall} filer lagt i {landing}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Kildetabellene
# MAGIC Ett view per kildetabell over filene i landing. Hvorfor view, og hvilke kolonner: se `tools/kildetabeller.py`.

# COMMAND ----------

for setning in sql_for_kildene(KATALOG, SKJEMA, VOLUM, landing):
    spark.sql(setning)

rader = []
for kilde, (_, _, _, tabeller) in KILDER.items():
    for t in tabeller:
        navn = f"{KATALOG}.{kildeskjema(SKJEMA, kilde)}.{t}"
        rader.append((navn, spark.table(navn).count()))
display(spark.createDataFrame(rader, "kildetabell string, rader long"))

# COMMAND ----------

print(f"""Ferdig: skjemaet {KATALOG}.{SKJEMA} er satt opp.
Neste steg: modul 2, steg 1 (moduler/M2.md). Der henter du kildetabellene inn i Specly fra katalogen {KATALOG},
skjemaene {kildeskjema(SKJEMA, "varius")} og {kildeskjema(SKJEMA, "kassio")}. Importen ber om et personlig tilgangstoken
fra Databricks. Kan du ikke lage token, har steget en omvei uten: CSV-filen kilder/kildetabeller_m2.csv.""")