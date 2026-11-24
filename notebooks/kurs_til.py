# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Sett alt til starten av en modul (nettlesersporet)
# MAGIC
# MAGIC Det samme som `./kurs til M<n>` i terminalsporet. Virker for hvilken som helst modul, også bakover.
# MAGIC
# MAGIC 1. Modellen i `specly/` i Git-mappen din (tabellene, begrepene, dataproduktet, kildesystemene og tabelltypene)
# MAGIC    kommer fra startpunktet (`.startpunkter/start-M<n>.startpunkt`, eller `fasit/M<n>` for sluttpunktet).
# MAGIC 2. Koden genereres, pipelinen kjøres med full refresh, og taggene settes (det samme som `kurs_generer_kjor`).
# MAGIC 3. Tabeller i skjemaet ditt uten kontrakt i startpunktet slettes.
# MAGIC
# MAGIC **«Bekreft»:** Går noe tapt (filer i modellen som er ulike startpunktet, eller tabeller som slettes), viser
# MAGIC notebooken listen og stopper før noe er endret. Se over listen, sett «Bekreft» til `ja`, og kjør på nytt.
# MAGIC Går ingenting tapt, er det ingenting å bekrefte: da kjører notebooken rett gjennom, også med «Bekreft» = `nei`.
# MAGIC Etter en vellykket kjøring setter notebooken «Bekreft» tilbake til `nei`, så neste kjøring viser listen igjen.
# MAGIC
# MAGIC **Velg «Til» før du kjører.** Standarden er `start/M4`. Skal du til en annen modul og har notebooken ingen felt
# MAGIC ennå: kjør bare cellen «Feltene» rett under denne (▶ øverst til venstre i cellen), velg «Til» i sidepanelet
# MAGIC «Parameters», vent til knappen «Run all» er tilbake, og trykk «Run all». Listen «Til» viser ikke alle valgene:
# MAGIC rull ned i listen for `fasit/…`, klikk på valget, og se at feltet viser det du valgte.
# MAGIC
# MAGIC **Feltene (parametere):** Første gang du åpner notebooken, og etter hver «Pull» i Git-mappen, har den ingen
# MAGIC felt («No parameters»). Trykk «Run all»: den kjører med standardverdiene («Til» = `start/M4`, «Bekreft» = `nei`, katalog `workspace`, skjema `toppfart` og volum `landing`), og etterpå
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
# MAGIC
# MAGIC Etterpå: commit og push i Git-mappen (trykk på branchnavnet øverst i Git-mappen, skriv en melding og «Commit & Push»), og «Import og eksport» → «Importer fra Git» → «Hent inn til …» i Specly. Se over
# MAGIC listen før du henter inn. Resten av `specly/Config` og `.specly/` er knyttet til ditt Specly-prosjekt og
# MAGIC endres ikke.
# MAGIC
# MAGIC Dette finnes bare fordi det er et kurs: i et ekte prosjekt finnes ingen startpunkter.

# COMMAND ----------

# Feltene. Cellen lager bare feltene i sidepanelet «Parameters» og endrer ingenting. Den står for seg selv og først, så
# du kan kjøre bare den (▶) og sette feltene før resten av notebooken kjører. Finnes feltene fra før, beholder de verdien.
PUNKTER = [f"{t}/M{m}" for t in ("start", "fasit") for m in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)]
dbutils.widgets.dropdown("til", "start/M4", PUNKTER, "Til")
dbutils.widgets.text("katalog", "workspace", "Katalog")
dbutils.widgets.text("skjema", "toppfart", "Skjema")
dbutils.widgets.text("volum", "landing", "Volum")
dbutils.widgets.dropdown("bekreft", "nei", ["nei", "ja"], "Bekreft (skriv over og slett)")

# COMMAND ----------

# MAGIC %md
# MAGIC Installasjonen under kan skrive rød tekst, for eksempel «Note: you may need to restart the kernel …» eller noe
# MAGIC om «pip's dependency resolver» og `mlflow-skinny`. Den er ufarlig: notebooken starter Python på nytt selv i
# MAGIC neste celle, og kurset bruker ikke mlflow.

# COMMAND ----------

# MAGIC %pip install -q datacontract-cli==1.2.10 pyyaml

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

TIL = dbutils.widgets.get("til")
KATALOG = dbutils.widgets.get("katalog")
SKJEMA = dbutils.widgets.get("skjema")
VOLUM = dbutils.widgets.get("volum")
BEKREFT = dbutils.widgets.get("bekreft") == "ja"

import os
import subprocess
import sys

from databricks.sdk import WorkspaceClient

ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
import generer
import kurspipeline
from kursmoduler import bytt_til, det_som_endres, startpunkt_mappe

assert os.path.isdir(f"/Volumes/{KATALOG}/{SKJEMA}/{VOLUM}"), \
    f"Fant ikke volumet /Volumes/{KATALOG}/{SKJEMA}/{VOLUM}. Kjør kurs_oppsett for skjemaet {SKJEMA} først."

W = WorkspaceClient()
# Eier terminalsporet skjemaet, stopper notebooken her, før modellen i specly/ er byttet og før noe er slettet.
opptatt = kurspipeline.terminalsporet_eier(W, KATALOG, SKJEMA)
assert not opptatt, opptatt

SPECLY = os.path.join(ROT, "specly")
KILDE = startpunkt_mappe(*TIL.split("/"))  # pakket ut fra .startpunkter/<start|fasit>-M<n>.startpunkt
assert KILDE, f"Fant ikke startpunktet {TIL}."


def kontrakter(specly):
    """{tabellnavn: sti relativt til specly/} for kontraktene i specly/Tables."""
    funnet = {}
    for mappe, _, filer in os.walk(os.path.join(specly, "Tables")):
        for f in filer:
            if f.endswith(".odcs.yaml"):
                funnet[f[: -len(".odcs.yaml")]] = os.path.relpath(os.path.join(mappe, f), specly)
    return funnet


def uten_kontrakt(med_kontrakt):
    """Tabellene i ditt eget skjema som ikke har kontrakt. Rører aldri andre skjemaer.
    Samme liste som `databricks tables list` i terminalsporet (Unity Catalog), uten pipelinens interne tabeller."""
    tabeller, token = [], None
    while True:
        side = W.api_client.do("GET", "/api/2.1/unity-catalog/tables", query={
            "catalog_name": KATALOG, "schema_name": SKJEMA, "max_results": 100, **({"page_token": token} if token else {})})
        tabeller += side.get("tables", [])
        token = side.get("next_page_token")
        if not token:
            break
    return sorted((t["name"], t.get("table_type", "")) for t in tabeller if t["name"] not in med_kontrakt)


NYE = kontrakter(KILDE)
print(f"Setter alt til {TIL}: {len(NYE)} tabeller i modellen ({KATALOG}.{SKJEMA}). Bekreft = {'ja' if BEKREFT else 'nei'}.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dette går tapt
# MAGIC Filer i modellen som ikke er like i startpunktet (ligger de i Git, finner du dem igjen der), og
# MAGIC tabeller i skjemaet ditt uten kontrakt i startpunktet.

# COMMAND ----------

tapt = [f"specly/{sti}  ({'finnes ikke i ' if hva == 'slettes' else 'ulik '}{TIL}, {hva})"
        for sti, hva in det_som_endres(KILDE, SPECLY)]
slettes = uten_kontrakt(set(NYE))
liste = "\n".join([f"  {linje}" for linje in tapt] + [f"  {KATALOG}.{SKJEMA}.{n}  ({typ}, slettes)" for n, typ in slettes])
print(liste or "Ingenting går tapt.")
if liste and not BEKREFT:
    # Teksten vises som resultatet av notebooken (utskrifter i samme celle kan bli borte når notebooken stopper).
    filer = "1 fil" if len(tapt) == 1 else f"{len(tapt)} filer"
    tabeller = "1 tabell" if len(slettes) == 1 else f"{len(slettes)} tabeller"
    dbutils.notebook.exit(f"Stoppet: {filer} og {tabeller} går tapt hvis du setter alt til {TIL}:\n{liste}\n"
                          "Ingenting er endret. Vil du fortsette: sett «Bekreft» til ja i sidepanelet «Parameters», vent "
                          "til knappen «Run all» er tilbake, og trykk «Run all».\n"
                          "Står det utskrift i cellene under, er den fra en tidligere kjøring.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Modellen fra startpunktet

# COMMAND ----------

# Tabellene, begrepene, dataproduktet, kildesystemene (start/M2 er uten formatet modul 2 ber deg fylle ut) og
# tabelltypene (kravene fra modul 8). Samme kode som ./kurs til (tools/kursmoduler.py).
bytt_til(KILDE, SPECLY)
print(f"Modellen i specly/ er nå {TIL}: {len(kontrakter(SPECLY))} kontrakter.")
r = subprocess.run([sys.executable, os.path.join(SPECLY, ".specly", "specly.py"), "check"], capture_output=True, text=True)
print("specly.py check: " + ((r.stdout + r.stderr).strip().splitlines() or [""])[-1])
assert r.returncode == 0, (r.stdout + r.stderr)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Generer og kjør (full refresh: alle tabellene bygges på nytt fra leveransene i landing)

# COMMAND ----------

w = W
if NYE:
    assert generer.generer(dc=[sys.executable, "-m", "datacontract.cli"]), "Forhåndssjekken stoppet. Se meldingen over."
    pid = kurspipeline.lag_eller_oppdater(w, ROT, KATALOG, SKJEMA, VOLUM)
    tilstand = kurspipeline.kjor(w, pid, full=True)
    assert tilstand == "COMPLETED", f"Pipelinen endte med {tilstand}. Se feilene over."
    print(f"{kurspipeline.sett_tags(spark, ROT, KATALOG, SKJEMA)} setninger for tags.")
else:
    # Tom modell: ingenting å generere eller kjøre. De gamle genererte filene fjernes, og pipelinen får ingen tabeller.
    ut = os.path.join(ROT, "databricks", "pyspark", "tabeller")
    for f in os.listdir(ut):
        if f.endswith(".py"):
            os.remove(os.path.join(ut, f))
    kurspipeline.lag_eller_oppdater(w, ROT, KATALOG, SKJEMA, VOLUM)
    print("Tom modell: ingen kode generert, pipelinen er ikke kjørt.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Tabeller uten kontrakt

# COMMAND ----------

ekstra = uten_kontrakt(set(NYE))
if not ekstra:
    print("Ingen.")
for n, typ in ekstra:
    hva = {"MATERIALIZED_VIEW": "MATERIALIZED VIEW", "VIEW": "VIEW"}.get(typ, "TABLE")
    spark.sql(f"DROP {hva} IF EXISTS {KATALOG}.{SKJEMA}.{n}")
    print(f"slettet {KATALOG}.{SKJEMA}.{n}")
ferdig = TIL  # settes først her, når alt over har gått

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ferdig
# MAGIC De to neste cellene setter «Bekreft» tilbake til `nei`: feltet fjernes og lages på nytt, fordi Databricks ikke lar en
# MAGIC notebook endre verdien i et felt. Neste kjøring viser derfor listen over det som går tapt, før noe endres.

# COMMAND ----------

dbutils.widgets.remove("bekreft")

# COMMAND ----------

dbutils.widgets.dropdown("bekreft", "nei", ["nei", "ja"], "Bekreft (skriv over og slett)")

# COMMAND ----------

print(f"""Ferdig: modellen og Databricks står på {ferdig}.
«Bekreft» er satt tilbake til nei. Står feltet likevel på ja i sidepanelet «Parameters», sett det til nei selv.
Neste steg: commit og push i Git-mappen (trykk på branchnavnet øverst i Git-mappen, skriv en melding og «Commit & Push»), og «Import og eksport» → «Importer fra Git» → «Hent inn til …» i Specly.
Se over listen før du henter inn.""")