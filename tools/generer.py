#!/usr/bin/env python3
"""Forhåndssjekk og kodegenerering fra kontraktene. Det ./generer og notebooks/kurs_generer_kjor gjør.

  uv run --no-project --with pyyaml python3 tools/generer.py      (det er det ./generer kjører)
  SPECLY=<mappe> UT=<mappe> KONSTANTER=<fil> TAGS=<fil> DATACONTRACT=<program> som miljøvariabler

1. tools/modell.py samler kryss-fakta (oppstrøm, relasjoner, kildesystemenes format, standardkolonner) til modell.j2.
2. tools/forhandssjekk.py stopper med en norsk melding hvis en kontrakt mangler noe malene trenger (nivå «kode»), eller
   noe prosjektet har gjort påkrevd (nivå «styring»). Da skrives ingenting.
3. Én `datacontract export custom` per kontrakt, med malen for tabelltypen (maler/pyspark/<type>.py.j2),
   til <UT>/<tabell>.py. Konstantene fra maler/pyspark/plattform.j2 går til <KONSTANTER>, og taggene i Unity Catalog
   for alle tabellene (maler/pyspark/tags.py.j2, modul 8) til <TAGS>. Ingen etterbehandling: filene er det malen skrev.
Snakker ikke med Databricks. Stier er relative til repoet.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROT, "tools"))
import forhandssjekk  # noqa: E402
import modell  # noqa: E402


def datacontract_standard():
    """Programmet ./generer bruker: DATACONTRACT, ellers ~/.local/bin/datacontract, ellers det som ligger på PATH
    eller ved siden av Python (slik %pip install legger det i en Databricks-notebook)."""
    if os.environ.get("DATACONTRACT"):
        return [os.environ["DATACONTRACT"]]
    for kandidat in (os.path.expanduser("~/.local/bin/datacontract"),
                     os.path.join(os.path.dirname(sys.executable), "datacontract"),
                     shutil.which("datacontract")):
        if kandidat and os.path.exists(kandidat):
            return [kandidat]
    return None


def _maler_med_modell(tmp, specly):
    """Malene kopiert til tmp/maler, med modell.j2 fra kontraktene i specly. Gir (malmappen, modellen)."""
    maler = os.path.join(tmp, "maler")
    shutil.copytree(os.path.join(ROT, "maler", "pyspark"), maler)
    m = modell.last_modell(specly)
    with open(os.path.join(maler, "modell.j2"), "w", encoding="utf-8") as fh:
        fh.write(modell.j2(m))
    return maler, m


def _eksporter(dc, mal, kontrakt):
    """Én `datacontract export custom`. Gir (teksten, None) eller (None, feilmeldingen)."""
    # Data Contract CLI skriver med Rich. Rich tror den skriver til en terminal når FORCE_COLOR er satt (som i
    # Databricks-notebooks), og fargelegger da koden med ANSI-koder. TTY_COMPATIBLE=0 skrur det av.
    miljo = {k: v for k, v in os.environ.items() if k != "FORCE_COLOR"}
    miljo.update(TTY_COMPATIBLE="0", NO_COLOR="1")
    # stdout (ikke --output): print() gir filen den avsluttende linjeskiftet.
    r = subprocess.run([*dc, "export", "custom", "--template", mal, kontrakt], capture_output=True, text=True, env=miljo)
    if r.returncode != 0:
        return None, f"{os.path.relpath(kontrakt, ROT)}: datacontract export feilet\n{r.stdout[-1500:]}{r.stderr[-1500:]}"
    if "\x1b" in r.stdout:
        return None, f"{os.path.relpath(kontrakt, ROT)}: datacontract export skrev terminalkoder (ANSI) i koden. Ingenting er skrevet."
    return r.stdout, None


def tags_for(specly, dc=None):
    """Taggene kontraktene i specly gir (maler/pyspark/tags.py.j2), som (TAGS, EIDE_NOKLER), uten å skrive noe.
    ./kurs sjekk og notebooks/kurs_sjekk sammenligner taggene i Databricks med dem fasit gir (modul 8)."""
    dc = dc or datacontract_standard()
    if not dc:
        sys.exit("Fant ikke Data Contract CLI. Installer den med: uv tool install datacontract-cli==1.2.10 (eller sett DATACONTRACT).")
    with tempfile.TemporaryDirectory() as tmp:
        maler, m = _maler_med_modell(tmp, specly)
        if not m["tabeller"]:
            return {}, []
        forste = next(iter(m["tabeller"].values()))["fil"]
        tekst, feil = _eksporter(dc, os.path.join(maler, "tags.py.j2"), os.path.join(os.path.dirname(specly), forste))
    if feil:
        sys.exit(feil)
    navnerom = {}
    # Filen er generert av malen vår og har bare to konstanter (TAGS og EIDE_NOKLER).
    exec(compile(tekst, "tags_data.py", "exec"), navnerom)  # noqa: S102
    return navnerom["TAGS"], navnerom["EIDE_NOKLER"]


TOM_MODELL = """Modellen har ingen tabeller ennå: det ligger ingen kontrakter (.odcs.yaml) i specly/Tables.
Ingenting er generert, og ingenting er sendt til Databricks.
Gjør dette: eksporter tabellene fra Specly («Import og eksport» → «Eksporter til Git»), hent dem hit
(nettlesersporet: «Pull» i Git-mappen, terminalsporet: git pull), og kjør på nytt."""


def antall_kontrakter(specly="specly"):
    """Antall kontrakter (.odcs.yaml) i specly/Tables. Null betyr tom modell: da er det ingenting å generere."""
    return sum(f.endswith(".odcs.yaml") for _, _, filer in os.walk(os.path.join(ROT, specly, "Tables")) for f in filer)


def generer(specly="specly", ut="databricks/pyspark/tabeller",
            konstanter="databricks/pyspark/plattform/konstanter.py", tags="databricks/pyspark/plattform/tags_data.py",
            dc=None):
    """Gir True når koden er generert, False når forhåndssjekken stoppet eller modellen er tom (da er ingenting
    skrevet)."""
    specly, ut, konstanter, tags = (os.path.join(ROT, p) for p in (specly, ut, konstanter, tags))
    dc = dc or datacontract_standard()
    if not dc:
        sys.exit("Fant ikke Data Contract CLI. Installer den med: uv tool install datacontract-cli==1.2.10 (eller sett DATACONTRACT).")

    with tempfile.TemporaryDirectory() as tmp:
        maler, m = _maler_med_modell(tmp, specly)
        # Gjennom JSON, slik forhandssjekk.py leser modellen når den kjøres alene.
        m = json.loads(json.dumps(m, ensure_ascii=False))
        if not m["tabeller"]:
            # Uten tabeller har malene ingen kontrakt å lese fra. Si hva som mangler, i stedet for å feile lenger ned.
            print(TOM_MODELL)
            return False

        # Begge nivåene kjøres, så du ser alt som mangler på én gang.
        feil = forhandssjekk.sjekk(m)
        styring_paa, feil_styring = forhandssjekk.sjekk_styring(specly)
        if feil:
            forhandssjekk.meld(feil)
        if feil_styring:
            forhandssjekk.meld(feil_styring, "styring")
        if feil or feil_styring:
            return False
        print("       Forhåndssjekk (kode): ingen mangler.")
        forhandssjekk.meld_styring_ok(styring_paa)

        kontraktmappe = os.path.dirname(specly)
        jobber = [(f"{t['navn']}.py", f"{t['mal']}.py.j2", t["fil"]) for t in m["tabeller"].values()]
        # Filene for hele plattformen. Malene bruker ikke kontrakten de får, bare modell.j2 og plattform.j2.
        felles = [("konstanter.py", "konstanter.py.j2", jobber[0][2]), ("tags_data.py", "tags.py.j2", jobber[0][2])]
        jobber += felles
        utmappe = os.path.join(tmp, "ut")
        os.makedirs(utmappe)

        def eksporter(jobb):
            navn, mal, fil = jobb
            tekst, feil = _eksporter(dc, os.path.join(maler, mal), os.path.join(kontraktmappe, fil))
            if feil:
                return feil
            with open(os.path.join(utmappe, navn), "w", encoding="utf-8") as fh:
                fh.write(tekst)
            return None

        # Hver eksport er en egen prosess; flere samtidig gjør det raskere uten å endre resultatet.
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
            feilet = [x for x in pool.map(eksporter, jobber) if x]
        if feilet:
            sys.exit("\n".join(feilet) + "\nGenereringen feilet. Ingenting er skrevet.")

        # Mappen er generert i sin helhet. Alle filer fjernes, også `.gitkeep` fra kursrepoet: pipelinen leser alt i
        # mappen (glob tabeller/**), og Databricks stopper på en fil som ikke er .py eller .sql
        # (UNSUPPORTED_LIBRARY_FILE_TYPE).
        os.makedirs(ut, exist_ok=True)
        for f in os.listdir(ut):
            if os.path.isfile(os.path.join(ut, f)):
                os.remove(os.path.join(ut, f))
        for navn, _, _ in jobber[:-len(felles)]:
            shutil.copyfile(os.path.join(utmappe, navn), os.path.join(ut, navn))
        for navn, til in (("konstanter.py", konstanter), ("tags_data.py", tags)):
            os.makedirs(os.path.dirname(til), exist_ok=True)
            shutil.copyfile(os.path.join(utmappe, navn), til)
    print(f"       {len(jobber) - len(felles)} tabeller generert i {os.path.relpath(ut, ROT)}/")
    return True


def main():
    ok = generer(os.environ.get("SPECLY", "specly"), os.environ.get("UT", "databricks/pyspark/tabeller"),
                 os.environ.get("KONSTANTER", "databricks/pyspark/plattform/konstanter.py"),
                 os.environ.get("TAGS", "databricks/pyspark/plattform/tags_data.py"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
