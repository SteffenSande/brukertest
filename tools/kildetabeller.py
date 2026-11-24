"""Kildetabellene deltakeren importerer i Specly med «Importer fra Databricks» (modul 0 og 2).

Brukt av `./kurs oppsett` (tools/kurs.py) og notebooks/kurs_oppsett.py.

I virkeligheten finnes kildesystemene fra før. Her later vi som: ett skjema per kilde, `<skjema>_kilde_<kilde>`
(standard `toppfart_kilde_kassio`), med ett VIEW per kildetabell over filene i landingsvolumet.

Hvorfor VIEW og ikke tabell: «Importer fra Databricks» leser bare metadata fra Unity Catalog
(`GET /api/2.1/unity-catalog/tables/<navn>`: navn, kolonner, typer, kommentar), aldri dataene, og viser VIEW
like gjerne som tabeller (~/specly: packages/server-core/src/services/databricksService.ts, getTableDetails).
Et VIEW koster ingenting å lage, viser alltid det som ligger i landing, og må aldri bygges på nytt.

Kolonnene er kildens kolonner slik de var da kilden ble tatt inn (overskriften i den første leveransen), alle
som tekst, akkurat som raw-kontraktene. Kolonner som kommer senere (campaignCode fra 1. oktober, H10), er
derfor ikke med: raw tar vare på dem i systemkolonnen sys__ukjente_kolonner (modul 3 viser det). Parquet har egne typer.

Dataene: kilder med fullt uttrekk viser bare den siste leveransen (slik systemet ser ut nå). Kilder som
leverer endringer eller daglige filer, viser alle leveransene.
"""
import json
import os

# kilde: (format, skilletegn, uttrekk, [tabeller]). Formatet står i kildearkene.
KILDER = {
    "varius": ("csv", ";", "fullt", ["vare", "varegruppe", "aktor"]),
    "kassio": ("csv", ",", "endringer", ["kvittering", "kvitteringslinje"]),
    "kalender": ("csv", ",", "fullt", ["dag"]),
    "nettora": ("json", None, "endringer", ["ordrelinje"]),
    "lojal": ("json", None, "fullt", ["medlem"]),
    "lagra": ("parquet", None, "endringer", ["beholdning"]),
}


def kildeskjema(skjema, kilde):
    return f"{skjema}_kilde_{kilde}"


def kolonner_i_forste_fil(mappe, tabell, filformat, skilletegn):
    """Kolonnenavnene i den første leveransen (filene sorteres på navn, som har tidspunktet i seg)."""
    filer = sorted(f for f in os.listdir(mappe) if f.startswith(tabell + "_") and f.endswith("." + filformat))
    if not filer:
        raise SystemExit(f"Fant ingen {filformat}-filer for {tabell} i {mappe}.")
    with open(os.path.join(mappe, filer[0]), encoding="utf-8") as f:
        forste = f.readline()
    if filformat == "csv":
        return [k.strip() for k in forste.strip().split(skilletegn)]
    return list(json.loads(forste))


def sql_for_kildene(katalog, skjema, volum, landing_lokalt):
    """SQL-setningene som lager kildeskjemaene og viewene. `landing_lokalt` er en mappe med de samme filene som
    volumet (data/landing i terminalsporet, volumet selv i notebooken); bare overskriftene leses derfra."""
    setninger = []
    for kilde, (filformat, skilletegn, uttrekk, tabeller) in KILDER.items():
        ks = f"{katalog}.{kildeskjema(skjema, kilde)}"
        setninger.append(f"CREATE SCHEMA IF NOT EXISTS {ks} COMMENT 'Kurs: later som kildesystemet {kilde}. "
                         f"Viewene leser filene i /Volumes/{katalog}/{skjema}/{volum}/{kilde}.'")
        for tabell in tabeller:
            filer = f"/Volumes/{katalog}/{skjema}/{volum}/{kilde}/{tabell}/{tabell}_*.{filformat}"
            valg = [f"format => '{filformat}'"]
            utvalg = "*"
            if filformat == "parquet":
                utvalg = "* EXCEPT (_rescued_data)"
            else:
                kolonner = kolonner_i_forste_fil(os.path.join(landing_lokalt, kilde, tabell), tabell, filformat, skilletegn)
                skjemastreng = ", ".join(f"`{k}` STRING" for k in kolonner)
                valg.append(f"schema => '{skjemastreng}'")
                if filformat == "csv":
                    valg += ["header => true", f"sep => '{sql_tekst(skilletegn)}'"]
            les = f"read_files('{filer}', {', '.join(valg)})"
            if uttrekk == "fullt":
                sporring = (f"WITH leveranser AS (SELECT {utvalg}, _metadata.file_name AS fil FROM {les})\n"
                            f"SELECT * EXCEPT (fil) FROM leveranser WHERE fil = (SELECT max(fil) FROM leveranser)")
                kommentar = "siste leveranse (fullt uttrekk)"
            else:
                sporring = f"SELECT {utvalg} FROM {les}"
                kommentar = "alle leveransene"
            setninger.append(f"CREATE OR REPLACE VIEW {ks}.{tabell}\nCOMMENT 'Kildetabellen {tabell} i {kilde}: "
                             f"{kommentar}.'\nAS {sporring}")
    return setninger


def sql_tekst(tegn):
    return tegn.replace("'", "\\'")
