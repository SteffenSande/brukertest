"""Pipelinen i nettlesersporet: det `databricks bundle deploy` og `databricks bundle run` gjør i terminalsporet (./kjor).

Brukes av notebooks/kurs_generer_kjor og notebooks/kurs_til. Innstillingene er de samme som pipelinen i
databricks.yml (serverless, development, katalog, skjema, root_path, configuration, libraries). Forskjellen:
koden ligger i Git-mappen din i stedet for i bundle-mappen, og pipelinen heter «Specly-kurs <skjema> (notebook)»
så den ikke blandes med den terminalsporet lager («Specly-kurs <skjema>»).

Kaller Databricks REST API med innloggingen notebooken allerede har (WorkspaceClient). Ingen token.
"""
import importlib
import os
import sys
import time

FERDIG = ("COMPLETED", "FAILED", "CANCELED")


def navn(skjema):
    return f"Specly-kurs {skjema} (notebook)"


def bundle_navn(skjema):
    return f"Specly-kurs {skjema}"


def _alle(w):
    svar, token = [], None
    while True:
        side = w.api_client.do("GET", "/api/2.0/pipelines",
                               query={"max_results": 100, **({"page_token": token} if token else {})})
        svar += side.get("statuses", [])
        token = side.get("next_page_token")
        if not token:
            return svar


def finn(w, pipelinenavn):
    treff = [p for p in _alle(w) if p.get("name") == pipelinenavn]
    return treff[0]["pipeline_id"] if treff else None


def spesifikasjon(rot, katalog, skjema, volum):
    """Det samme som resources.pipelines.toppfart i databricks.yml. `rot` er Git-mappen (/Workspace/...)."""
    kode = f"{rot}/databricks/pyspark"
    return {
        "name": navn(skjema),
        "serverless": True,
        "development": True,
        "catalog": katalog,
        "schema": skjema,
        # Mappen legges i sys.path, så tabellfilene kan importere funksjonspakken `plattform`.
        "root_path": kode,
        "configuration": {
            "plattform.landing": f"/Volumes/{katalog}/{skjema}/{volum}",
            # salg_dato regnes fra UTC til norsk tid med from_utc_timestamp, som forutsetter at økten står i UTC.
            "spark.sql.session.timeZone": "UTC",
        },
        # Generert fra kontraktene. Ikke rediger for hånd.
        "libraries": [{"glob": {"include": f"{kode}/tabeller/**"}}],
    }


def terminalsporet_eier(w, katalog, skjema):
    """Norsk melding når terminalsporets pipeline finnes for skjemaet, ellers None. Notebookene spør før de endrer noe
    (modellen i specly/, den genererte koden, pipelinen), og stopper med meldingen."""
    annen = finn(w, bundle_navn(skjema))
    if not annen:
        return None
    return (f"Skjemaet {katalog}.{skjema} har allerede pipelinen «{bundle_navn(skjema)}» fra terminalsporet ({annen}).\n"
            "En tabell kan bare eies av én pipeline. Ingenting er endret. Velg én av disse:\n"
            "  a) Fortsett i terminalsporet (./kurs og ./kjor).\n"
            "  b) Bruk et annet skjema i nettlesersporet: kjør kurs_oppsett med det nye skjemanavnet i feltet «Skjema»\n"
            "     først, og bruk samme skjema i de andre notebookene.\n"
            "  c) Slett den pipelinen (Jobs & Pipelines) og tabellene den laget, og kjør på nytt.")


def lag_eller_oppdater(w, rot, katalog, skjema, volum):
    """Gir pipeline-id. Lager pipelinen første gang, ellers oppdateres den til innstillingene over."""
    opptatt = terminalsporet_eier(w, katalog, skjema)
    if opptatt:
        raise SystemExit(opptatt)
    spec = spesifikasjon(rot, katalog, skjema, volum)
    pid = finn(w, spec["name"])
    if pid:
        w.api_client.do("PUT", f"/api/2.0/pipelines/{pid}", body={"id": pid, **spec})
        print(f"Oppdaterte pipelinen «{spec['name']}» ({pid}).")
    else:
        pid = w.api_client.do("POST", "/api/2.0/pipelines", body=spec)["pipeline_id"]
        print(f"Laget pipelinen «{spec['name']}» ({pid}).")
    return pid


def kjor(w, pid, full=False, vent=15):
    """Starter en oppdatering og venter til den er ferdig. Gir sluttilstanden (COMPLETED, FAILED eller CANCELED)."""
    uid = w.api_client.do("POST", f"/api/2.0/pipelines/{pid}/updates", body={"full_refresh": bool(full)})["update_id"]
    print(f"Update ID: {uid}{' (full refresh: alle tabeller bygges på nytt)' if full else ''}")
    forrige, start = None, time.time()
    while True:
        tilstand = w.api_client.do("GET", f"/api/2.0/pipelines/{pid}/updates/{uid}")["update"]["state"]
        if tilstand != forrige:
            print(f"  {int(time.time() - start):4d} s  {tilstand}")
            forrige = tilstand
        if tilstand in FERDIG:
            break
        time.sleep(vent)
    print(f"Update {uid} is {tilstand}")
    if tilstand != "COMPLETED":
        for melding in feilmeldinger(w, pid, uid):
            print(f"  - {melding}")
    return tilstand


def feilmeldinger(w, pid, uid, antall=10):
    svar = w.api_client.do("GET", f"/api/2.0/pipelines/{pid}/events",
                           query={"filter": "level='ERROR'", "max_results": 50})
    meldinger = []
    for e in svar.get("events", []):
        if (e.get("origin") or {}).get("update_id") not in (uid, None):
            continue
        tekst = e.get("message", "")
        for x in (e.get("error") or {}).get("exceptions", [])[:1]:
            tekst += f"\n      {x.get('class_name', '')}: {(x.get('message') or '')[:600]}"
        meldinger.append(tekst)
    return meldinger[:antall]


def sett_tags(spark, rot, katalog, skjema):
    """Taggene i Unity Catalog etter kontraktene (modul 8), når pipelinen er ferdig: det tools/sett_tags.py gjør i ./kjor.
    Leser databricks/pyspark/plattform/tags_data.py på nytt, siden ./generer kan ha skrevet den i denne økten.
    Gir antall setninger som ble kjørt."""
    kode = os.path.join(rot, "databricks", "pyspark")
    if kode not in sys.path:
        sys.path.insert(0, kode)
    tags = importlib.reload(importlib.import_module("plattform.tags"))
    data = importlib.reload(importlib.import_module("plattform.tags_data"))
    return tags.sett_tags(spark, katalog, skjema, data.TAGS, data.EIDE_NOKLER)
