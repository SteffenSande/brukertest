# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Sjekk mot fasit (nettlesersporet)
# MAGIC
# MAGIC Det samme som `./kurs sjekk M<n>` i terminalsporet:
# MAGIC
# MAGIC 1. Modellen i `specly/` (slik Specly eksporterte den til Git) mot fasit for modulen: kontraktene (det koden
# MAGIC    trenger; id-er og beskrivelser teller ikke), fra modul 9 forretningsbegrepene og fra modul 10 dataproduktet.
# MAGIC 2. Tallene i tabellene dine mot fasit, for modul 2 til og med modulen du velger.
# MAGIC 3. Fra modul 8: kravene, eier, granularitet og klassifisering i kontraktene, og taggene i Unity Catalog mot dem
# MAGIC    fasit gir.
# MAGIC
# MAGIC Husk å hente siste versjon av repoet (Git-mappen: «Pull») etter at du har eksportert fra Specly.
# MAGIC
# MAGIC **Resultatet står i den siste cellen**, nederst: linjene om kontraktene (fra modul 9 også begrepene, fra modul 10
# MAGIC dataproduktet), tallene («Fasittest (modul 2-N): … riktige, … feil.») og taggene. Utskriftene lenger opp er
# MAGIC detaljene. De står i bokser du kan rulle i.
# MAGIC
# MAGIC **Feltene (parametere):** Første gang du åpner notebooken, og etter hver «Pull» i Git-mappen, har den ingen
# MAGIC felt («No parameters»). Trykk «Run all». Notebooken lager feltene og stopper uten å sjekke noe («Velg modul»).
# MAGIC Feltene ligger nå i sidepanelet «Parameters» (knappen «Show parameters»). Velg modulen din i feltet «Modul», vent
# MAGIC til knappen «Run all» er tilbake, og trykk «Run all» igjen. Katalogen `workspace` og skjemaet `toppfart` er
# MAGIC riktig for de fleste.
# MAGIC
# MAGIC **Vil du ha et annet skjema enn `toppfart`?** Skriv skjemanavnet i feltet «Skjema» i sidepanelet «Parameters» og
# MAGIC trykk Enter, samtidig som du velger modul. Vent til knappen «Run all» er tilbake, og trykk «Run all».
# MAGIC
# MAGIC **Når du har endret et felt:** Databricks kjører cellen som leser feltene på nytt av seg selv. Mens den går, står det
# MAGIC «Interrupt» der «Run all» pleier å stå. Vent til «Run all» er tilbake før du trykker. Trykker du for tidlig, blir
# MAGIC kjøringen avbrutt («Cancelled») og ingenting annet kjører. Utskriftene du ser, er da fra forrige kjøring.
# MAGIC
# MAGIC Feltet «Modul» viser ikke alle valgene: rull ned i listen for `M9`, `M10` og `M11`, klikk på valget, og se at
# MAGIC feltet viser det du valgte. Står feltet på en senere modul enn du er kommet til, melder sjekken tabeller som
# MAGIC mangler. Står det på en tidligere, sjekkes ikke det modulen din handler om.

# COMMAND ----------

# Feltene. Cellen lager bare feltene i sidepanelet «Parameters» og endrer ingenting. Den står for seg selv og først, så
# du kan kjøre bare den (▶) og sette feltene før resten av notebooken kjører. Finnes feltene fra før, beholder de verdien.
# Den står også for seg selv fordi Databricks ikke viser et felt som lages i samme celle som notebooken stopper i
# (dbutils.notebook.exit, i cellen under).
# Standardvalget sjekker ingenting. Feltet finnes ikke før første kjøring (og er borte etter «Pull»), så en standard
# som var en modul, ville sjekket den modulen uansett hvilken modul du er i.
VELG = "Velg modul"
dbutils.widgets.dropdown("modul", VELG, [VELG] + [f"M{m}" for m in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)], "Modul")
dbutils.widgets.text("katalog", "workspace", "Katalog")
dbutils.widgets.text("skjema", "toppfart", "Skjema")

# COMMAND ----------

if dbutils.widgets.get("modul") == "Velg modul":
    # Egen celle, etter cellen som lager feltene: da er feltene tegnet i sidepanelet når notebooken stopper her.
    dbutils.notebook.exit("Ingenting er sjekket. Velg modulen din i feltet «Modul» i sidepanelet «Parameters» "
                          "(knappen «Show parameters»; rull ned i listen for M9, M10 og M11), vent til knappen «Run all» "
                          "er tilbake, og trykk «Run all» igjen. Står det utskrift i cellene under, er den fra en "
                          "tidligere kjøring.")

# COMMAND ----------

# MAGIC %md
# MAGIC Installasjonen under kan skrive rød tekst, for eksempel «Note: you may need to restart the kernel …» eller noe
# MAGIC om «pip's dependency resolver» og `mlflow-skinny`. Den er ufarlig: notebooken starter Python på nytt selv i
# MAGIC neste celle, og kurset bruker ikke mlflow.

# COMMAND ----------

# MAGIC %pip install -q datacontract-cli==1.2.10 pyyaml

# COMMAND ----------

# Data Contract CLI (taggene fasit gir, fra modul 8) kan ha byttet ut pakker. Start Python på nytt så de nye brukes.
dbutils.library.restartPython()

# COMMAND ----------

# Etter restartPython leses feltet på nytt. «Velg modul» stoppet notebooken i cellen over installasjonen.
assert dbutils.widgets.get("modul") != "Velg modul", "Velg modulen din i feltet «Modul» i sidepanelet «Parameters», og trykk «Run all» igjen."
MODUL = int(dbutils.widgets.get("modul").lstrip("M"))
KATALOG = dbutils.widgets.get("katalog")
SKJEMA = dbutils.widgets.get("skjema")

import os
import sys

ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
from kursmoduler import STYRING_I_MODUL, startpunkt_mappe
from sammenlign import avvik_tags, sjekk_modell, tagglinje
import generer
import test_fasit_lokalt as fasittest

print(f"Sjekker modul 2-{MODUL} i {KATALOG}.{SKJEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Modellen mot fasit
# MAGIC Kontraktene, fra modul 9 også forretningsbegrepene, og fra modul 10 dataproduktet.

# COMMAND ----------

fasit = startpunkt_mappe("fasit", MODUL)  # pakket ut fra .startpunkter/fasit-M<n>.startpunkt
funn, modellinjer = [], []
# Samme kode som ./kurs sjekk: kontraktene (med styringen fra modul 8), begrepene (modul 9) og dataproduktet (modul 10).
for _, avvikene, linje in sjekk_modell(os.path.join(ROT, "specly"), fasit, MODUL):
    for f in avvikene:
        print(f"- {f}")
    print(linje)
    funn += avvikene
    modellinjer.append(linje)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Tallene mot fasit

# COMMAND ----------

spark.sql(f"USE {KATALOG}.{SKJEMA}")
fasittest.kjor_sjekker(lambda q: [tuple(r) for r in spark.sql(q).collect()], MODUL)
ok, feil = fasittest.RESULTAT["ok"], fasittest.RESULTAT["feil"]
tallinje = f"Fasittest (modul 2-{MODUL}): {ok} riktige, {feil} feil."
print(tallinje)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Taggene mot fasit (fra modul 8)

# COMMAND ----------

tags = []
if MODUL >= STYRING_I_MODUL:
    fasit_tags, eide = generer.tags_for(fasit, dc=[sys.executable, "-m", "datacontract.cli"])
    tags, mangler = avvik_tags(spark, KATALOG, SKJEMA, fasit_tags, eide)
    for f in tags:
        print(f"- {f}")
    tagglinjen = tagglinje(tags, mangler, len(fasit_tags), "kurs_generer_kjor")
else:
    tagglinjen = f"Modul {MODUL} har ingen tags å sjekke (tags kommer i modul 8)."
print(tagglinjen)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resultatet
# MAGIC Linjene under er hele resultatet. Detaljene står i cellene over.

# COMMAND ----------

print(f"Sjekk av modul 2-{MODUL} i {KATALOG}.{SKJEMA}:")
print(f"  1. {modellinjer[0]}")
for linje in modellinjer[1:]:  # begrepene (fra modul 9) og dataproduktet (fra modul 10)
    print(f"     {linje}")
print(f"  2. {tallinje}")
print(f"  3. {tagglinjen}")
assert not funn and not feil and not tags, "Noe avviker fra fasit. Se linjene over, og detaljene i cellene lenger opp."
print("Alt stemmer med fasit.")