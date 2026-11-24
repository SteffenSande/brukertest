# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Fyll inn tabellene modulen ikke ber deg lage (nettlesersporet)
# MAGIC
# MAGIC Det samme som `./kurs fyll M<n>` i terminalsporet. Legger kontraktene fra fasit for modulen inn i
# MAGIC `specly/Tables` i Git-mappen din, og kjører `specly.py check`. Etterpå: commit og push i Git-mappen
# MAGIC (trykk på branchnavnet øverst i Git-mappen, skriv en melding og «Commit & Push»), og «Import og eksport» → «Importer fra Git» → «Hent inn til …» i Specly.
# MAGIC
# MAGIC **Feltet «Modul»:** Første gang du åpner notebooken, og etter hver «Pull» i Git-mappen, har den ikke noe felt
# MAGIC («No parameters»). Trykk «Run all». Notebooken lager feltet og stopper uten å endre noe («Velg modul»). Feltet
# MAGIC «Modul» ligger nå i sidepanelet «Parameters» (knappen «Show parameters»). Velg modulen din der, vent til knappen
# MAGIC «Run all» er tilbake, og trykk «Run all» igjen. Notebooken har ikke felt for katalog og skjema: den skriver bare i
# MAGIC Git-mappen, ikke i Databricks.
# MAGIC
# MAGIC **Når du har endret feltet:** Databricks kjører cellen som leser feltet på nytt av seg selv. Mens den går, står det
# MAGIC «Interrupt» der «Run all» pleier å stå. Trykker du «Run all» for tidlig, blir kjøringen avbrutt («Cancelled») og
# MAGIC ingenting annet kjører. Utskriftene du ser, er da fra forrige kjøring.
# MAGIC
# MAGIC **Husk:** fyll går an fordi kurset har bestemt forretningsbehovet og har en fasit. I et ekte prosjekt
# MAGIC finnes ingen fasit å fylle fra. Modellen lages ut fra hva forretningen trenger, og det er det kurset
# MAGIC øver på.

# COMMAND ----------

# Feltet «Modul». Cellen lager bare feltet i sidepanelet «Parameters» og endrer ingenting. Den står for seg selv:
# Databricks viser ikke et felt som lages i samme celle som notebooken stopper i (dbutils.notebook.exit).
# Valgene er modulene som har noe å fylle (FYLL i tools/kursmoduler.py), de samme som ./kurs fyll godtar.
# Standardvalget fyller ingenting. Feltet finnes ikke før første kjøring (og er borte etter «Pull»), så en standard
# som var en modul, ville fylt for den modulen uansett hvilken modul du er i.
import os
import sys

ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
from kursmoduler import FYLL

VELG = "Velg modul"
dbutils.widgets.dropdown("modul", VELG, [VELG] + [f"M{m}" for m in sorted(FYLL)], "Modul")

# COMMAND ----------

# MAGIC %md
# MAGIC Installasjonen under kan skrive rød tekst («Note: you may need to restart the kernel …»). Den er ufarlig.

# COMMAND ----------

# MAGIC %pip install -q pyyaml

# COMMAND ----------

import os
import shutil
import subprocess
import sys

ROT = os.path.dirname(os.getcwd())
assert os.path.isdir(os.path.join(ROT, "tools")), f"Fant ikke tools/ under {ROT}. Kjør notebooken fra repoet (Git-mappen)."
sys.path.insert(0, os.path.join(ROT, "tools"))
from kursmoduler import FYLL, TABELLER_PER_MODUL, startpunkt_mappe

VELG = "Velg modul"
if dbutils.widgets.get("modul") == VELG:
    # Egen celle, etter cellen som lager feltet: da er feltet tegnet i sidepanelet når notebooken stopper her.
    dbutils.notebook.exit("Ingenting er endret. Velg modulen din i feltet «Modul» i sidepanelet «Parameters» "
                          "(knappen «Show parameters»), vent til knappen «Run all» er tilbake, og trykk «Run all» igjen. "
                          "Står det utskrift i cellen under, er den fra en tidligere kjøring.")
MODUL = int(dbutils.widgets.get("modul").lstrip("M"))
print(f"Fyller for modul {MODUL}.")


def kontrakter(specly):
    funnet = {}
    for mappe, _, filer in os.walk(os.path.join(specly, "Tables")):
        for f in filer:
            if f.endswith(".odcs.yaml"):
                funnet[f[: -len(".odcs.yaml")]] = os.path.relpath(os.path.join(mappe, f), specly)
    return funnet

# COMMAND ----------

SPECLY = os.path.join(ROT, "specly")
fasit = startpunkt_mappe("fasit", MODUL)  # pakket ut fra .startpunkter/fasit-M<n>.startpunkt
fra, har = kontrakter(fasit), kontrakter(SPECLY)
lagt_inn = []
for t in FYLL[MODUL]:
    if t in har:
        print(f"{t}: finnes allerede ({har[t]}), lar den være")
        continue
    til = os.path.join(SPECLY, fra[t])
    os.makedirs(os.path.dirname(til), exist_ok=True)
    shutil.copyfile(os.path.join(fasit, fra[t]), til)
    lagt_inn.append(t)
    print(f"{t}: lagt inn som specly/{fra[t]}")

r = subprocess.run([sys.executable, os.path.join(SPECLY, ".specly", "specly.py"), "check"], capture_output=True, text=True)
print((r.stdout + r.stderr).strip())
if r.returncode == 0 and "--apply-rules" in r.stdout + r.stderr:
    print("(Linjen om «fix --apply-rules» er til orientering. Du trenger ikke gjøre noe.)")
egne = [t for t in TABELLER_PER_MODUL[MODUL] if t not in FYLL[MODUL] and t not in kontrakter(SPECLY)]
# Forklaringen står i selve feilmeldingen: den vises alltid, også når utskriften over er lang og må rulles.
hjelp = (f" Tabellene fyll la inn, peker på tabeller modul {MODUL} ber deg lage selv, og som ikke finnes ennå: "
         f"{', '.join(egne)}. Lag dem i Specly, eksporter til Git, «Pull», og kjør på nytt. Da forsvinner feilen.") if egne else ""
assert r.returncode == 0, "specly.py check fant feil. Se meldingen over." + hjelp

# COMMAND ----------

if lagt_inn:
    print(f"Ferdig: {len(lagt_inn)} tabeller lagt inn for modul {MODUL}.")
    print("Neste steg: commit og push i Git-mappen (trykk på branchnavnet øverst i Git-mappen), og «Import og eksport» → «Importer fra Git» → «Hent inn til …» i Specly.")
else:
    print(f"Ferdig: ingenting nytt å legge inn for modul {MODUL}. Ingenting å committe.")