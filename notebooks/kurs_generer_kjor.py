# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Generer og kjør (nettlesersporet)
# MAGIC
# MAGIC Det samme som `./kjor` i terminalsporet, og det et ekte prosjekt også ville gjort:
# MAGIC
# MAGIC 1. **Forhåndssjekk og generering** fra kontraktene i `specly/` i Git-mappen din, med Data Contract CLI og
# MAGIC    malene i `maler/`. Akkurat det `./generer` gjør (`tools/generer.py`). Koden havner i
# MAGIC    `databricks/pyspark/tabeller/` i Git-mappen.
# MAGIC 2. **Pipelinen** «Specly-kurs &lt;skjema&gt; (notebook)» lages eller oppdateres, med de samme innstillingene som
# MAGIC    `databricks.yml` (det terminalsporet ruller ut med `databricks bundle deploy`).
# MAGIC 3. **Kjøring**: pipelinen bygger tabellene i skjemaet ditt. Notebooken venter og viser resultatet.
# MAGIC 4. **Tags** i Unity Catalog etter kontraktene (eier og klassifisering, modul 8). Pipelinen kan ikke sette tags
# MAGIC    selv, så det er et eget steg når den er ferdig (`databricks/pyspark/plattform/tags.py`).
# MAGIC
# MAGIC Før første gang: `kurs_oppsett` (skjema, landingsvolum og filene). Husk «Pull» i Git-mappen etter at du
# MAGIC har eksportert fra Specly, så notebooken ser de siste kontraktene. Kjør på serverless. Ingen token trengs.
# MAGIC Har modellen ingen tabeller ennå, stopper notebooken og sier det, uten å endre noe.
# MAGIC
# MAGIC **Feltene (parametere):** Første gang du åpner notebooken, og etter hver «Pull» i Git-mappen, har den ingen
# MAGIC felt («No parameters»). Trykk «Run all»: den kjører med standardverdiene (katalog `workspace`, skjema `toppfart`, volum `landing` og ingen full refresh), og etterpå
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
# MAGIC Bruk samme skjema som i `kurs_oppsett`.

# COMMAND ----------

# Feltene. Cellen lager bare feltene i sidepanelet «Parameters» og endrer ingenting. Den står for seg selv og først, så
# du kan kjøre bare den (▶) og sette feltene før resten av notebooken kjører. Finnes feltene fra før, beholder de verdien.
dbutils.widgets.text("katalog", "workspace", "Katalog")
dbutils.widgets.text("skjema", "toppfart", "Skjema")
dbutils.widgets.text("volum", "landing", "Volum")
dbutils.widgets.dropdown("full", "nei", ["nei", "ja"], "Full refresh (bygg alle tabeller på nytt)")

# COMMAND ----------

# MAGIC %md
# MAGIC Installasjonen under kan skrive rød tekst, for eksempel «Note: you may need to restart the kernel …» eller noe
# MAGIC om «pip's dependency resolver» og `mlflow-skinny`. Den er ufarlig: notebooken starter Python på nytt selv i
# MAGIC neste celle, og kurset bruker ikke mlflow.

# COMMAND ----------

# MAGIC %pip install -q datacontract-cli==1.2.10 pyyaml

# COMMAND ----------

# Data Contract CLI kan ha byttet ut pakker Python allerede har lastet. Start Python på nytt så de nye brukes.
dbutils.library.restartPython()

# COMMAND ----------

KATALOG = dbutils.widgets.get("katalog")
SKJEMA = dbutils.widgets.get("skjema")
VOLUM = dbutils.widgets.get("volum")
FULL = dbutils.widgets.get("full") == "ja"

import os
import sys

from databricks.sdk import WorkspaceClient

# Notebooken ligger i notebooks/ i repoet; verktøyene i tools/.
ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
import generer
import kurspipeline

assert os.path.isdir(f"/Volumes/{KATALOG}/{SKJEMA}/{VOLUM}"), \
    f"Fant ikke volumet /Volumes/{KATALOG}/{SKJEMA}/{VOLUM}. Kjør kurs_oppsett for skjemaet {SKJEMA} først."
w = WorkspaceClient()
# Eier terminalsporet skjemaet, stopper notebooken her, før noe er generert eller endret.
opptatt = kurspipeline.terminalsporet_eier(w, KATALOG, SKJEMA)
assert not opptatt, opptatt
print(f"Git-mappe {ROT}\nSkjema {KATALOG}.{SKJEMA}, volum {VOLUM}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Forhåndssjekk og generering
# MAGIC Stopper forhåndssjekken, skrives ingenting og ingenting sendes til pipelinen. Rett kontrakten i Specly,
# MAGIC eksporter til Git, «Pull» i Git-mappen, og kjør på nytt.

# COMMAND ----------

if not generer.antall_kontrakter():
    # Tom modell (før første eksport i modul 2, eller «Pull» mangler). Notebooken stopper uten feil, med meldingen som resultat.
    dbutils.notebook.exit(generer.TOM_MODELL + "\nStår det utskrift i cellene under, er den fra en tidligere kjøring.")
# Data Contract CLI kjøres som `python -m datacontract.cli`, med Python-en %pip installerte den for.
ok = generer.generer(dc=[sys.executable, "-m", "datacontract.cli"])
assert ok, "Forhåndssjekken stoppet. Se meldingen over. Ingenting er generert eller sendt til Databricks."

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Pipelinen og kjøringen

# COMMAND ----------

pid = kurspipeline.lag_eller_oppdater(w, ROT, KATALOG, SKJEMA, VOLUM)
tilstand = kurspipeline.kjor(w, pid, full=FULL)
assert tilstand == "COMPLETED", f"Pipelinen endte med {tilstand}. Se feilene over, og pipelinen under Jobs & Pipelines."

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Tags i Unity Catalog

# COMMAND ----------

antall = kurspipeline.sett_tags(spark, ROT, KATALOG, SKJEMA)
print(f"{antall} setninger for tags i {KATALOG}.{SKJEMA}" + ("" if antall else " (alt stod riktig fra før)"))

# COMMAND ----------

tabeller = spark.sql(f"SHOW TABLES IN {KATALOG}.{SKJEMA}").filter("isTemporary = false").count()
print(f"Ferdig: {tabeller} tabeller i {KATALOG}.{SKJEMA}. Sjekk tallene med notebooken kurs_sjekk.")
print("Koden i databricks/pyspark/tabeller/ er endret i Git-mappen hvis kontraktene er endret. Commit og push den")
print("gjerne (branchnavnet øverst i Git-mappen, «Commit & Push»), så viser Git koden som kjører. Den lages uansett på nytt fra kontraktene hver gang.")