#!/usr/bin/env python3
"""Kurskommandoene bak ./kurs. Kjøres med ./kurs, som starter dette skriptet med uv.

  ./kurs oppsett            bundle deploy (skjema og landingsvolum), laster opp data/landing, lager kildetabellene
  ./kurs til M4             modellen fra start/M4, tabeller uten kontrakt fjernes, ./kjor --full
  ./kurs til fasit/M5       det samme, til sluttpunktet for modul 5
  ./kurs fyll M3            legger inn tabellene modul 3 ikke ber deg lage selv (også M4, M5, M6, M7 og M11)
  ./kurs fyll M4            legger inn tabellene modul 4 ikke ber deg lage selv, fra fasit/M4
  ./kurs sjekk M4           kontraktene mot fasit/M4, og tallene i Databricks for modul 2 til og med 4
  ./kurs sjekk M8           i tillegg eier, granularitet og klassifisering, og taggene i Databricks
  ./kurs sjekk M10          i tillegg forretningsbegrepene (fra modul 9) og dataproduktet (fra modul 10)
  --ja                      svar ja på spørsmålene (for skript); uten --ja spør kommandoene før de sletter noe

Miljø: DATABRICKS_PROFILE (standard kurs), KATALOG (workspace), SKJEMA (toppfart), VOLUM (landing).

Nettlesersporet har én notebook per kommando: notebooks/kurs_oppsett, kurs_til, kurs_fyll og
kurs_sjekk, og notebooks/kurs_generer_kjor for ./generer og ./kjor. Notebookene lager sin egen pipeline
(«Specly-kurs <skjema> (notebook)», tools/kurspipeline.py) i stedet for bundle deploy.

Det kommandoene gjør, står rett i koden under, med de samme Databricks- og Git-kommandoene du ville skrevet
selv. De rører bare modellen i specly/ (FRA_STARTPUNKTET i tools/kursmoduler.py: Tables, Concepts, DataProducts,
kildesystemene og tabelltypene), de genererte filene og ditt eget skjema (og kildeskjemaene <skjema>_kilde_*).
Startpunktene ligger pakket i .startpunkter/<start|fasit>-M<n>.startpunkt (tools/startpunkter.py lager dem). Resten av
specly/Config, .specly.json og .specly/ er knyttet til ditt Specly-prosjekt, og endres aldri av ./kurs.
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kildetabeller import KILDER, kildeskjema, sql_for_kildene  # noqa: E402
from kursmoduler import (BEGREPER_I_MODUL, FYLL, MODULER, STYRING_I_MODUL, TABELLER_PER_MODUL, bytt_til,  # noqa: E402
                         det_som_endres, startpunkt_mappe)
from sammenlign import avvik_tags, hva_sjekkes, sjekk_modell, tagglinje  # noqa: E402

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFIL = os.environ.get("DATABRICKS_PROFILE", "kurs")
KATALOG = os.environ.get("KATALOG", "workspace")
SKJEMA = os.environ.get("SKJEMA", "toppfart")
VOLUM = os.environ.get("VOLUM", "landing")
SPECLY = os.path.join(ROT, "specly")
GENERERT = os.path.join(ROT, "databricks", "pyspark", "tabeller")
JA = "--ja" in sys.argv

FYLL_PAMINNELSE = """Husk: fyll går an fordi kurset har bestemt forretningsbehovet og har en fasit. I et ekte
prosjekt finnes ingen fasit å fylle fra. Modellen lages ut fra hva forretningen trenger, og det er det kurset
øver på."""

# Commit-meldingen «Neste steg» foreslår etter fyll, der modulteksten bruker en annen enn «fyll M<n>».
FYLL_MELDING = {6: "Nettbutikken: raw via Git, bronze med fyll"}


def kjor(*cmd, **kw):
    """Kjører en kommando og viser den først, så du ser hva som skjer."""
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=ROT, **kw)


def databricks(*args, json_ut=False):
    r = subprocess.run(["databricks", *args, "-p", PROFIL] + (["-o", "json"] if json_ut else []),
                       cwd=ROT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Databricks CLI feilet: databricks {' '.join(args)}\n{r.stderr.strip()}")
    return json.loads(r.stdout) if json_ut else r.stdout


def sql():
    """SQL mot SQL warehouse i arbeidsflaten (samme vei som fasittesten)."""
    from test_fasit_lokalt import databricks_sql
    return databricks_sql(PROFIL, KATALOG, SKJEMA)


def utrulling_feilet(r):
    """Avslutter med utskriften fra bundle deploy. Finnes skjemaet fra før (laget av notebooken kurs_oppsett i
    nettlesersporet), kommer veien ut på norsk i tillegg til feilen fra Databricks."""
    tekst = f"{r.stdout}{r.stderr}\nUtrullingen feilet."
    if "SCHEMA_ALREADY_EXISTS" in tekst:
        var = f"--var=katalog={KATALOG} --var=skjema={SKJEMA} --var=volum={VOLUM}"
        tekst += f"""

Skjemaet {KATALOG}.{SKJEMA} finnes fra før, men er ikke laget av terminalsporet. Trolig er oppsettet gjort
med notebooken kurs_oppsett (nettlesersporet). Sporene kan ikke blandes i samme skjema. Velg én av disse:
  a) Fortsett i nettlesersporet: bruk notebookene i Databricks i stedet for ./kurs og ./kjor.
  b) La terminalsporet overta skjemaet og volumet. Filene i volumet blir liggende. Gjør det bare hvis
     pipelinen «Specly-kurs {SKJEMA} (notebook)» ikke finnes under Jobs & Pipelines:
       databricks bundle deployment bind skjema {KATALOG}.{SKJEMA} -p {PROFIL} {var} --auto-approve
       databricks bundle deployment bind landing {KATALOG}.{SKJEMA}.{VOLUM} -p {PROFIL} {var} --auto-approve
     Kjør så samme kommando på nytt."""
    sys.exit(tekst)


def spor(tekst):
    if JA:
        print(f"{tekst} [j/N] j (--ja)")
        return True
    if not sys.stdin.isatty():
        sys.exit(f"{tekst}\nIngen terminal å spørre i. Kjør på nytt med --ja for å svare ja.")
    return input(f"{tekst} [j/N] ").strip().lower() in ("j", "ja", "y", "yes")


def kontrakter(specly):
    """{tabellnavn: sti relativt til specly/} for kontraktene i specly/Tables."""
    funnet = {}
    for mappe, _, filer in os.walk(os.path.join(specly, "Tables")):
        for f in filer:
            if f.endswith(".odcs.yaml"):
                funnet[f[: -len(".odcs.yaml")]] = os.path.relpath(os.path.join(mappe, f), specly)
    return funnet


def startpunkt(ref):
    """'M4' -> start/M4, 'start/M4' og 'fasit/M4' som de er. Gir (navn, mappen med specly/)."""
    ref = ref.strip("/")
    navn = ref if "/" in ref else f"start/{ref}"
    type_, _, m = navn.partition("/")
    m = m.upper()
    navn = f"{type_}/{m}"
    mappe = startpunkt_mappe(type_, m) if type_ in ("start", "fasit") and m[1:].isdigit() else None
    if not mappe:
        sys.exit(f"Ukjent startpunkt «{ref}». Bruk {', '.join(f'M{x}' for x in MODULER)}, start/M<n> eller fasit/M<n>.")
    return navn, mappe


def modulnummer(ref):
    try:
        m = int(ref.upper().lstrip("M"))
    except ValueError:
        m = None
    if m not in MODULER:
        sys.exit(f"Ukjent modul «{ref}». Bruk {', '.join(f'M{x}' for x in MODULER)}.")
    return m


def specly_check():
    r = subprocess.run([sys.executable, os.path.join(SPECLY, ".specly", "specly.py"), "check"],
                       cwd=ROT, capture_output=True, text=True)
    tekst = (r.stdout + r.stderr).strip()
    siste = (tekst.splitlines() or [""])[-1]
    print("  specly.py check: " + siste)
    if r.returncode == 0 and "--apply-rules" in siste:
        print("  (Linjen over er til orientering. Du trenger ikke gjøre noe.)")
    if r.returncode != 0:
        print(tekst)
    return r.returncode == 0


# ---------------------------------------------------------------------------------------------- oppsett
def oppsett():
    landing = os.path.join(ROT, "data", "landing")
    print(f"Oppsett i {KATALOG}.{SKJEMA} (profil {PROFIL})")
    if not os.path.isdir(landing):
        print("0/4  data/landing finnes ikke. Lager dataene (oppdiktet, deterministisk):")
        if kjor("uv", "run", "-q", "tools/lag_data.py").returncode != 0:
            sys.exit("Datageneratoren feilet.")

    print("1/4  Skjema og landingsvolum (bundle deploy)")
    r = kjor("databricks", "bundle", "deploy", "-p", PROFIL, f"--var=katalog={KATALOG}", f"--var=skjema={SKJEMA}",
             f"--var=volum={VOLUM}", "--auto-approve", capture_output=True, text=True)
    if r.returncode != 0:
        utrulling_feilet(r)

    volum = f"dbfs:/Volumes/{KATALOG}/{SKJEMA}/{VOLUM}"
    antall = sum(len(f) for _, _, f in os.walk(landing))
    print(f"2/4  Laster opp {antall} filer fra data/landing til {volum} (tar et par minutter)")
    r = kjor("databricks", "fs", "cp", "-r", "--overwrite", "data/landing", volum, "-p", PROFIL,
             capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{r.stderr}\nOpplastingen feilet.")

    print("3/4  Kildetabellene (ett skjema per kilde, ett view per tabell over filene i landing)")
    kjor_sql = sql()
    for setning in sql_for_kildene(KATALOG, SKJEMA, VOLUM, landing):
        kjor_sql(setning)
        if setning.startswith("CREATE OR REPLACE VIEW"):
            print("       " + setning.split("\n")[0].removeprefix("CREATE OR REPLACE VIEW "))

    print("4/4  Kontroll: rader per kildetabell")
    for kilde, (_, _, _, tabeller) in KILDER.items():
        for t in tabeller:
            navn = f"{KATALOG}.{kildeskjema(SKJEMA, kilde)}.{t}"
            print(f"       {navn}: {kjor_sql(f'SELECT count(*) FROM {navn}')[0][0]} rader")
    print(f"""Ferdig. Neste steg: modul 2, steg 1 (moduler/M2.md). Der henter du kildetabellene inn i Specly fra katalogen
{KATALOG}, skjemaene {SKJEMA}_kilde_varius og {SKJEMA}_kilde_kassio. Importen ber om et personlig tilgangstoken fra
Databricks. Kan du ikke lage token, har steget en omvei uten: CSV-filen kilder/kildetabeller_m2.csv.""")


# ---------------------------------------------------------------------------------------------- til
def til(ref):
    navn, kilde = startpunkt(ref)
    nye = kontrakter(kilde)
    print(f"Setter alt til {navn}: {len(nye)} tabeller i modellen ({KATALOG}.{SKJEMA}, profil {PROFIL})")

    # 1. Modellen: tabellene, begrepene, dataproduktet, kildesystemene (start/M2 er uten formatet modul 2 ber deg fylle
    # ut) og tabelltypene (kravene fra modul 8). Det som går tapt, er filer der som ikke er like i startpunktet.
    tapt = [f"  specly/{sti}  ({'finnes ikke i ' if hva == 'slettes' else 'ulik '}{navn}, {hva})"
            for sti, hva in det_som_endres(kilde, SPECLY)]
    print(f"1/4  Modellen (tabeller, begreper, dataprodukter, kildesystemer og tabelltyper) fra startpunktet {navn}")
    if tapt:
        print("     Dette går tapt (ligger det i Git, finner du det igjen der):")
        print("\n".join(tapt))
        if not spor("     Skrive over?"):
            sys.exit("Avbrutt. Ingenting er endret.")
    bytt_til(kilde, SPECLY)
    specly_check()

    # 2. Generer, rull ut og kjør. Full refresh: alle tabellene bygges på nytt fra leveransene i landing.
    print("2/4  Generer, rull ut og kjør pipelinen")
    if nye:
        if kjor("./kjor", "--full", env=dict(os.environ, SKJEMA=SKJEMA, DATABRICKS_PROFILE=PROFIL)).returncode != 0:
            sys.exit("./kjor feilet. Se meldingen over.")
    else:
        # Tom modell: ingenting å generere. De gamle genererte filene fjernes, og bundle deploy tar dem ut av pipelinen.
        for f in os.listdir(GENERERT):
            if f.endswith(".py"):
                os.remove(os.path.join(GENERERT, f))
        r = kjor("databricks", "bundle", "deploy", "-p", PROFIL, f"--var=katalog={KATALOG}", f"--var=skjema={SKJEMA}",
                 f"--var=volum={VOLUM}", "--auto-approve", capture_output=True, text=True)
        if r.returncode != 0:
            utrulling_feilet(r)

    # 3. Tabeller i ditt skjema uten kontrakt i startpunktet.
    print(f"3/4  Tabeller i {KATALOG}.{SKJEMA} uten kontrakt i {navn}")
    rydd(set(nye))

    print(f"""4/4  Ferdig: modellen og Databricks står på {navn}.
Neste steg:
  git add specly && git commit -m "Til {navn.removeprefix('start/')}" && git push
  I Specly: «Import og eksport» → «Importer fra Git» → «Hent inn til …». Se over listen før du henter inn.""")


def rydd(med_kontrakt):
    """Fjerner tabeller i ditt eget skjema som ikke har kontrakt. Spør først. Rører aldri andre skjemaer."""
    tabeller = databricks("tables", "list", KATALOG, SKJEMA, json_ut=True) or []
    ekstra = [(t["name"], t.get("table_type", "")) for t in tabeller if t["name"] not in med_kontrakt]
    if not ekstra:
        print("     Ingen.")
        return
    for n, typ in ekstra:
        print(f"     {KATALOG}.{SKJEMA}.{n}  ({typ})")
    if not spor(f"     Slette disse {len(ekstra)} tabellene?"):
        print("     Lar dem stå.")
        return
    kjor_sql = sql()
    for n, typ in ekstra:
        hva = {"MATERIALIZED_VIEW": "MATERIALIZED VIEW", "VIEW": "VIEW"}.get(typ, "TABLE")
        kjor_sql(f"DROP {hva} IF EXISTS {KATALOG}.{SKJEMA}.{n}")
        print(f"     slettet {n}")


# ---------------------------------------------------------------------------------------------- fyll
def fyll(ref):
    m = modulnummer(ref)
    if m not in FYLL:
        sys.exit(f"Modul {m} har ingenting å fylle. fyll finnes for {', '.join(f'M{x}' for x in FYLL)}.")
    _, fasit = startpunkt(f"fasit/M{m}")
    fra = kontrakter(fasit)
    har = kontrakter(SPECLY)
    print(f"Fyller inn tabellene modul {m} ikke ber deg lage selv, fra fasit/M{m}")
    lagt_inn = []
    for t in FYLL[m]:
        if t in har:
            print(f"  {t}: finnes allerede ({har[t]}), lar den være")
            continue
        til_sti = os.path.join(SPECLY, fra[t])
        os.makedirs(os.path.dirname(til_sti), exist_ok=True)
        shutil.copy2(os.path.join(fasit, fra[t]), til_sti)
        lagt_inn.append(fra[t])
        print(f"  {t}: lagt inn som specly/{fra[t]}")
    ok = specly_check()
    egne = [t for t in TABELLER_PER_MODUL[m] if t not in FYLL[m] and t not in kontrakter(SPECLY)]
    if not ok and egne:
        print(f"""  Tabellene fyll la inn, peker på tabeller modul {m} ber deg lage selv, og som ikke finnes ennå:
  {', '.join(egne)}. Lag dem i Specly, så forsvinner feilen over.""")
    print()
    print(FYLL_PAMINNELSE)
    if lagt_inn:
        print(f"""
Neste steg:
  git add specly && git commit -m "{FYLL_MELDING.get(m, f'fyll M{m}')}" && git push
  I Specly: «Import og eksport» → «Importer fra Git» → «Hent inn til …». Fortsett så i modulteksten (moduler/M{m}.md).""")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------------------------------------- sjekk
def sjekk(ref):
    m = modulnummer(ref)
    _, fasit = startpunkt(f"fasit/M{m}")
    styring = m >= STYRING_I_MODUL
    steg = 3 if styring else 2
    print(f"Sjekker modul 2 til og med {m} mot fasit")
    print(f"1/{steg}  {'Modellen' if m >= BEGREPER_I_MODUL else 'Kontraktene'} i specly/ mot fasit/M{m} ({hva_sjekkes(m)})")
    funn = []
    for _, avvikene, linje in sjekk_modell(SPECLY, fasit, m):  # kontraktene, begrepene (modul 9) og dataproduktet (modul 10)
        for f in avvikene:
            print(f"  - {f}")
        print(f"     {linje}")
        funn += avvikene

    print(f"2/{steg}  Tallene i {KATALOG}.{SKJEMA} (fasittesten for modul 2-{m})")
    r = subprocess.run([sys.executable, os.path.join(ROT, "tools", "test_fasit_lokalt.py"), "--databricks", "--modul", str(m)],
                       cwd=ROT, env=dict(os.environ, DATABRICKS_PROFILE=PROFIL, KATALOG=KATALOG, SKJEMA=SKJEMA))

    tags = []
    if styring:
        # Taggene finnes bare i Databricks, så de sjekkes bare her (ikke i den lokale fasittesten).
        print(f"3/{steg}  Taggene i {KATALOG}.{SKJEMA} mot dem fasit/M{m} gir (eier og klassifisering)")
        from generer import tags_for
        fasit_tags, eide = tags_for(fasit)
        tags, mangler = avvik_tags(sql(), KATALOG, SKJEMA, fasit_tags, eide)
        for f in tags:
            print(f"  - {f}")
        print("     " + tagglinje(tags, mangler, len(fasit_tags), "./kjor"))
    sys.exit(1 if funn or tags or r.returncode else 0)


def main():
    sys.stdout.reconfigure(line_buffering=True)  # meldingene kommer i riktig rekkefølge med kommandoene under
    args = [a for a in sys.argv[1:] if a != "--ja"]
    kommandoer = {"oppsett": (oppsett, 0), "til": (til, 1), "fyll": (fyll, 1), "sjekk": (sjekk, 1)}
    if args and args[0] in ("-h", "--help", "hjelp"):
        print(__doc__)
        return
    if not args or args[0] not in kommandoer or len(args) != 1 + kommandoer[args[0]][1]:
        sys.exit(__doc__)
    funksjon, _ = kommandoer[args[0]]
    funksjon(*args[1:])


if __name__ == "__main__":
    main()
