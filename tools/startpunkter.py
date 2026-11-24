#!/usr/bin/env python3
"""Lager startpunktene (modul 2-11) fra den fulle modellen i specly/.

  uv run --no-project --with pyyaml python3 tools/startpunkter.py           lager og sjekker alle
  uv run --no-project --with pyyaml python3 tools/startpunkter.py --sjekk   lager og sjekker alle i en midlertidig mappe,
                                        og sier fra hvis .startpunkter/ ikke er lik (skriver ingenting)
  uv run --no-project --with pyyaml python3 tools/startpunkter.py --uten-generering   hopper over ./generer (raskere)

Skriver (alt slettes og lages på nytt; samme innhold gir byte-like filer):
  .startpunkter/fasit-M<n>.startpunkt   specly/ slik den er ved SLUTTEN av modul n
  .startpunkter/start-M<n>.startpunkt   specly/ slik den er ved STARTEN av modul n (alt fra modulene før: start/M8 =
                                        fasit/M7, start/M11 = fasit/M10)

Pakket, ikke løse filer: Specly leser alle .odcs.yaml i repoet som kontrakter, også utenfor specly/. Løse kopier
med de samme id-ene får Specly til å holde tilbake slettinger og endringer fra Git.
tools/kursmoduler.py (startpunkt_mappe) pakker ut ved behov.

Hvilke tabeller som hører til hvilken modul, står i tools/kursmoduler.py. Alt annet i specly/ (Config/,
.specly.json, .specly/, AGENTS.md, README.md) er likt i alle startpunktene, med disse unntakene:
  - start/M2 har ingen tabeller, og kildesystemene varius og kassio er uten format og regex-mønster (modul 2 steg 4)
  - før modul 8 har tabelltypene ingen påkrevde felt, og kontraktene har ingen eier, granularitet eller klassifisering
    (STYRING_I_MODUL; feltene selv er med fra start)
  - før modul 9 er det ingen begreper (Concepts/), og kolonnene som fikk begrepets tekst, har teksten fra før
    (BEGREPER_I_MODUL, KOLONNEBESKRIVELSE_FOR_MODUL). Koblinger til tabeller som ikke finnes, tas bort
  - før modul 10 er det ingen dataprodukter (DataProducts/), og kontraktene har ikke `dataProduct`
    (DATAPRODUKT_I_MODUL)
  - relasjoner som en senere modul ber deltakeren lage, er tatt ut (RELASJONER_I_MODUL)
  - kolonner, Beregning og tabellbeskrivelser som en senere modul legger til en tabell, er tatt ut (KOLONNER_I_MODUL,
    BEREGNING_I_MODUL, BESKRIVELSE_FOR_MODUL), og det samme er oppstrøm og «Union av» som peker på tabeller fra senere
    moduler (modul 6 gjør slv__salgslinje til en union med nettbutikken)

Hvert startpunkt sjekkes:
  1. specly.py check (det Specly selv sjekker før «Hent inn»): må gi 0 feil og 0 advarsler.
  2. ./generer mot startpunktet (forhåndssjekken og genereringen), der startpunktet har tabeller.
"""
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kursmoduler import (ARKIV, BEGREPER_I_MODUL, BEREGNING_I_MODUL, BESKRIVELSE_FOR_MODUL,  # noqa: E402
                         DATAPRODUKT_I_MODUL, KILDESYSTEM_FELT_I_MODUL_2, KILDESYSTEM_I_MODUL_2,
                         KOLONNEBESKRIVELSE_FOR_MODUL, KOLONNER_I_MODUL, MODULER, RELASJONER_I_MODUL, STYRING_I_MODUL,
                         STYRINGSFELT, STYRINGSKRAV, arkivfil, tabeller_til_og_med)
from modell import feltdefinisjoner, tabellnavn  # noqa: E402

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KILDE = os.path.join(ROT, "specly")


def alle_kontrakter(specly):
    """{tabellnavn: sti relativt til specly/} for alle kontraktene."""
    funnet = {}
    for mappe, _, filer in os.walk(os.path.join(specly, "Tables")):
        for f in filer:
            if f.endswith(".odcs.yaml"):
                funnet[f[: -len(".odcs.yaml")]] = os.path.relpath(os.path.join(mappe, f), specly)
    return funnet


def uten_relasjoner(tekst):
    """Kontrakten uten blokken `relationships:` på skjemaobjektet (fire mellomrom inn)."""
    ut, hopper = [], False
    for linje in tekst.splitlines(keepends=True):
        if linje.rstrip() == "    relationships:":
            hopper = True
            continue
        if hopper and linje.strip() and len(linje) - len(linje.lstrip()) <= 4 and not linje.lstrip().startswith("- "):
            hopper = False
        if hopper and (not linje.strip() or len(linje) - len(linje.lstrip()) > 4 or linje.startswith("      -")):
            continue
        hopper = False
        ut.append(linje)
    return "".join(ut)


class SpeclyYaml(yaml.SafeDumper):
    """YAML slik Specly skriver kontraktene: lister rykket inn under nøkkelen. Lest og skrevet igjen er en kontrakt
    byte-lik (prøvd på alle kontraktene), så specly.py check gir ingen formatadvarsel."""
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def dump(doc):
    return yaml.dump(doc, Dumper=SpeclyYaml, sort_keys=False, allow_unicode=True, width=10**9, default_flow_style=False)


def _camel(key):
    deler = key.split("_")
    return deler[0] + "".join(d[:1].upper() + d[1:] for d in deler[1:])


def _fjern_felt(obj, d):
    """Tar bort verdien av prosjektfeltet `d` (feltdefinisjonen) fra objektet, der Specly skriver den: som customProperty
    eller i ODCS-feltet odcsTarget (med punktum: ledd for ledd, og tomme foreldre tas bort). Gir True når noe ble tatt bort."""
    mal = d.get("odcsTarget") or "customProperties"
    if mal == "customProperties":
        navn = d.get("odcsPropertyName") or _camel(d["key"])
        felt = obj.get("customProperties") or []
        igjen = [c for c in felt if not (isinstance(c, dict) and c.get("property") == navn)]
        if len(igjen) == len(felt):
            return False
        if igjen:
            obj["customProperties"] = igjen
        else:
            del obj["customProperties"]
        return True
    ledd = mal.split(".")
    kjede = [obj]
    for x in ledd[:-1]:
        if not isinstance(kjede[-1].get(x), dict):
            return False
        kjede.append(kjede[-1][x])
    if ledd[-1] not in kjede[-1]:
        return False
    del kjede[-1][ledd[-1]]
    for forelder, x in zip(reversed(kjede[:-1]), reversed(ledd[:-1])):
        if forelder[x]:
            break
        del forelder[x]
    return True


def uten_felt(doc, defs, nokler):
    """Kontrakten (dict) uten verdiene av prosjektfeltene `nokler`, der feltdefinisjonene (`defs`) sier at de står: et
    kolonnefelt på hver kolonne, et tabellfelt på tabellen eller på roten av dokumentet (team.name). Gir True når noe
    ble tatt bort. Et felt prosjektet ikke har, hoppes over."""
    s = doc["schema"][0]
    endret = False
    for key in nokler:
        d = defs.get(key)
        if not d:
            continue
        for obj in (s.get("properties") or []) if "column" in d.get("entityTypes", []) else (s, doc):
            endret = _fjern_felt(obj, d) or endret
    return endret


def uten_krav(sti):
    """specly/Config/table_types.json uten kravene fra modul 8 (påkrevde felt per tabelltype)."""
    with open(sti, encoding="utf-8") as f:
        typer = json.load(f)
    for tt in typer:
        for k in STYRINGSKRAV:
            tt.pop(k, None)
    with open(sti, "w", encoding="utf-8") as f:
        f.write(json.dumps(typer, ensure_ascii=False, indent=2))


def uten_styring(specly):
    """specly/ slik den er før modul 8: ingen krav i prosjektoppsettet, og ingen eier, granularitet eller
    klassifisering i kontraktene. tester/test_forhandssjekk.py bruker den også."""
    defs = feltdefinisjoner(specly)
    for mappe, _, filer in os.walk(os.path.join(specly, "Tables")):
        for f in filer:
            if f.endswith(".odcs.yaml"):
                sti = os.path.join(mappe, f)
                with open(sti, encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                if uten_felt(doc, defs, STYRINGSFELT):
                    with open(sti, "w", encoding="utf-8") as fh:
                        fh.write(dump(doc))
    uten_krav(os.path.join(specly, "Config", "table_types.json"))


def for_modul(tekst, tabell, tabeller, siste_modul, defs):
    """Kontrakten slik den var ved slutten av `siste_modul`: uten kolonner, Beregning og beskrivelse fra senere moduler,
    uten oppstrøm og «Union av» som peker på tabeller som ikke finnes i startpunktet (`tabeller`), og uten styringsfeltene
    før modul 8 (`defs`: feltdefinisjonene). Uendret tekst når ingenting skal bort."""
    doc = yaml.safe_load(tekst)
    s = doc["schema"][0]
    endret = siste_modul < STYRING_I_MODUL and uten_felt(doc, defs, STYRINGSFELT)
    if siste_modul < DATAPRODUKT_I_MODUL and doc.pop("dataProduct", None) is not None:
        endret = True
    behold = [p for p in s["properties"] if KOLONNER_I_MODUL.get(f"{tabell}.{p['name']}", 0) <= siste_modul]
    if len(behold) != len(s["properties"]):
        s["properties"], endret = behold, True
    for p in s["properties"]:
        modul, beskrivelse = KOLONNEBESKRIVELSE_FOR_MODUL.get(f"{tabell}.{p['name']}", (0, None))
        if modul > siste_modul:
            p["description"], endret = beskrivelse, True
        if BEREGNING_I_MODUL.get(f"{tabell}.{p['name']}", 0) > siste_modul:
            for felt in ("transformLogic", "transformDescription"):
                if p.pop(felt, None) is not None:
                    endret = True
        opp = p.get("transformSourceObjects")
        if opp:
            igjen = [o for o in opp if o.rsplit(".", 1)[0] in tabeller]
            if igjen != opp:
                endret = True
                if igjen:
                    p["transformSourceObjects"] = igjen
                else:
                    del p["transformSourceObjects"]
    felt = s.get("customProperties") or []
    for c in list(felt):
        if c.get("property") == "unionAv":
            igjen = [x for x in tabellnavn(c.get("value")) if x in tabeller]
            if len(igjen) < 2:
                felt.remove(c)
                endret = True
            elif igjen != tabellnavn(c.get("value")):
                c["value"], endret = igjen, True
    modul, beskrivelse = BESKRIVELSE_FOR_MODUL.get(tabell, (0, None))
    if modul > siste_modul:
        s["description"], endret = beskrivelse, True
    if not endret:
        return tekst
    return dump(doc)


def lag_startpunkt(mal, tabeller, kontrakter, siste_modul):
    """Kopierer specly/ til mal/specly, med bare kontraktene i `tabeller`. Relasjoner som lages i en modul etter
    `siste_modul` (RELASJONER_I_MODUL), tas ut."""
    ut = os.path.join(mal, "specly")
    os.makedirs(os.path.dirname(ut), exist_ok=True)
    shutil.copytree(KILDE, ut, ignore=shutil.ignore_patterns("Tables", "__pycache__", ".DS_Store"))
    os.makedirs(os.path.join(ut, "Tables"))
    defs = feltdefinisjoner(KILDE)
    for t in tabeller:
        fra = os.path.join(KILDE, kontrakter[t])
        til = os.path.join(ut, kontrakter[t])
        os.makedirs(os.path.dirname(til), exist_ok=True)
        shutil.copy2(fra, til)
        with open(til, encoding="utf-8") as f:
            tekst = f.read()
        ny = for_modul(tekst, t, set(tabeller), siste_modul, defs)
        if RELASJONER_I_MODUL.get(t, 0) > siste_modul:
            ny = uten_relasjoner(ny)
        if ny != tekst:
            with open(til, "w", encoding="utf-8") as f:
                f.write(ny)
    if siste_modul < 2:
        uten_kildeformat(os.path.join(ut, "Config", "source_systems.json"))
    if siste_modul < STYRING_I_MODUL:
        uten_krav(os.path.join(ut, "Config", "table_types.json"))
    for mappe, modul, filtrer in (("Concepts", BEGREPER_I_MODUL, begrep_for), ("DataProducts", DATAPRODUKT_I_MODUL, dataprodukt_for)):
        sti = os.path.join(ut, mappe)
        if siste_modul < modul:
            shutil.rmtree(sti, ignore_errors=True)
            continue
        for f in sorted(os.listdir(sti)) if os.path.isdir(sti) else []:
            with open(os.path.join(sti, f), encoding="utf-8") as fh:
                tekst = fh.read()
            ny = filtrer(tekst, set(tabeller))
            if ny != tekst:
                with open(os.path.join(sti, f), "w", encoding="utf-8") as fh:
                    fh.write(ny)
    return ut


def begrep_for(tekst, tabeller):
    """En begrepsfil (specly/Concepts/<navn>.md) uten koblinger til tabeller som ikke finnes i startpunktet. Uendret tekst
    når ingenting skal bort."""
    _, topp, kropp = tekst.split("---\n", 2)
    data = yaml.safe_load(topp)
    koblinger = data.get("columns") or []
    igjen = [c for c in koblinger if (c if isinstance(c, str) else c.get("path", "")).split(".", 1)[0] in tabeller]
    if len(igjen) == len(koblinger):
        return tekst
    if igjen:
        data["columns"] = igjen
    else:
        data.pop("columns", None)
    return "---\n" + dump(data) + "---\n" + kropp


def dataprodukt_for(tekst, tabeller):
    """Et dataprodukt (specly/DataProducts/<navn>.odps.yaml) uten tabeller som ikke finnes i startpunktet."""
    doc = yaml.safe_load(tekst)
    endret = False
    for c in doc.get("customProperties") or []:
        if c.get("property") == "tables":
            igjen = [t for t in c["value"] if (t if isinstance(t, str) else t.get("name")) in tabeller]
            if igjen != c["value"]:
                c["value"], endret = igjen, True
    return dump(doc) if endret else tekst


def uten_kildeformat(sti):
    """start/M2: kildesystemene modul 2 fyller ut, uten format og regex-mønster (modul 2 steg 4)."""
    with open(sti, encoding="utf-8") as f:
        systemer = json.load(f)
    for s in systemer:
        if s["name"] in KILDESYSTEM_I_MODUL_2:
            for felt in KILDESYSTEM_FELT_I_MODUL_2:
                s.pop(felt, None)
    with open(sti, "w", encoding="utf-8") as f:
        f.write(json.dumps(systemer, ensure_ascii=False, indent=2))


def pakk(specly, fil):
    """Pakker mappen som specly/ i en zip med faste tidsstempler, så samme innhold gir samme fil (ingen støy i Git)."""
    os.makedirs(os.path.dirname(fil), exist_ok=True)
    rot = os.path.dirname(specly)
    with zipfile.ZipFile(fil, "w", zipfile.ZIP_DEFLATED) as z:
        for mappe, undermapper, filer in os.walk(specly):
            undermapper.sort()
            rel = os.path.relpath(mappe, rot)
            info = zipfile.ZipInfo(rel + "/", date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o40755 << 16) | 0x10  # mappe, rwxr-xr-x (uten x-bit kan unzip-mappene ikke åpnes)
            z.writestr(info, "")  # også tomme mapper (Tables/ i start/M2)
            for f in sorted(filer):
                info = zipfile.ZipInfo(os.path.join(rel, f), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                with open(os.path.join(mappe, f), "rb") as fh:
                    z.writestr(info, fh.read())


def sjekk(navn, specly, tabeller, generer):
    feil = []
    r = subprocess.run([sys.executable, os.path.join(specly, ".specly", "specly.py"), "check"],
                       capture_output=True, text=True, check=False)
    # Oppsummeringen («0 feil, 0 advarsler») kommer på stderr.
    siste = ((r.stdout + r.stderr).strip().splitlines() or [""])[-1]
    if r.returncode != 0 or siste != "0 feil, 0 advarsler":
        feil.append(f"specly.py check: {siste}\n{r.stdout}{r.stderr}")
    gen = "ingen tabeller, ingen generering"
    if tabeller and generer:
        with tempfile.TemporaryDirectory() as tmp:
            miljo = dict(os.environ, SPECLY=os.path.relpath(specly, ROT), UT=os.path.join(tmp, "ut"),
                         KONSTANTER=os.path.join(tmp, "konstanter.py"), TAGS=os.path.join(tmp, "tags_data.py"))
            g = subprocess.run(["./generer"], cwd=ROT, env=miljo, capture_output=True, text=True, check=False)
            antall = len(os.listdir(os.path.join(tmp, "ut"))) if os.path.isdir(os.path.join(tmp, "ut")) else 0
            if g.returncode != 0 or antall != len(tabeller):
                feil.append(f"./generer: {antall} filer for {len(tabeller)} tabeller\n{g.stdout}{g.stderr}")
            gen = f"./generer ok ({antall} tabeller)"
    elif tabeller:
        gen = "./generer hoppet over"
    print(f"  {navn:9} {len(tabeller):2} tabeller   specly.py check: {siste}   {gen}")
    return feil


def main():
    generer = "--uten-generering" not in sys.argv
    bare_sjekk = "--sjekk" in sys.argv
    kontrakter = alle_kontrakter(KILDE)
    mangler = [t for t in tabeller_til_og_med(max(MODULER)) if t not in kontrakter]
    ukjente = sorted(set(kontrakter) - set(tabeller_til_og_med(max(MODULER))))
    if mangler or ukjente:
        sys.exit(f"tools/kursmoduler.py og specly/ stemmer ikke overens. Mangler i specly/: {mangler}. "
                 f"Ikke plassert i en modul: {ukjente}. "
                 f"Står specly/ på et startpunkt etter ./kurs til? Kjør ./kurs til fasit/M{max(MODULER)} først.")
    with open(os.path.join(KILDE, "Config", "source_systems.json"), encoding="utf-8") as f:
        uten_format = [x["name"] for x in json.load(f) if not x.get("metadataValues") or not x.get("regexPattern")]
    if uten_format:
        sys.exit(f"Kildesystemene {uten_format} i specly/Config mangler format eller regex-mønster. Står specly/ på "
                 f"start/M2 etter ./kurs til? Kjør ./kurs til fasit/M{max(MODULER)} først.")
    with open(os.path.join(KILDE, "Config", "table_types.json"), encoding="utf-8") as f:
        if not any(k in tt for tt in json.load(f) for k in STYRINGSKRAV):
            sys.exit(f"specly/Config/table_types.json har ingen påkrevde felt (modul 8). Står specly/ på et startpunkt før "
                     f"modul 8 etter ./kurs til? Kjør ./kurs til fasit/M{max(MODULER)} først.")
    for mappe, modul in (("Concepts", BEGREPER_I_MODUL), ("DataProducts", DATAPRODUKT_I_MODUL)):
        if not os.path.isdir(os.path.join(KILDE, mappe)):
            sys.exit(f"specly/{mappe} finnes ikke (modul {modul}). Står specly/ på et startpunkt før modul {modul} etter "
                     f"./kurs til? Kjør ./kurs til fasit/M{max(MODULER)} først.")
    feil = []
    with tempfile.TemporaryDirectory() as tmp:
        arkiv = os.path.join(tmp, "arkiv") if bare_sjekk else ARKIV
        if not bare_sjekk:
            shutil.rmtree(ARKIV, ignore_errors=True)
        print(f"{'Sjekker' if bare_sjekk else 'Lager'} startpunktene i {os.path.relpath(ARKIV, ROT)}/")
        for m in MODULER:
            for type_, siste_modul in (("start", m - 1), ("fasit", m)):
                tabeller = tabeller_til_og_med(siste_modul)
                specly = lag_startpunkt(os.path.join(tmp, type_, f"M{m}"), tabeller, kontrakter, siste_modul)
                feil += sjekk(f"{type_}/M{m}", specly, tabeller, generer)
                fil = os.path.join(arkiv, os.path.basename(arkivfil(type_, m)))
                pakk(specly, fil)
                if bare_sjekk:
                    lagret = arkivfil(type_, m)
                    if not os.path.isfile(lagret) or not filecmp.cmp(lagret, fil, shallow=False):
                        feil.append(f"{os.path.relpath(lagret, ROT)} er ikke lik den som lages fra specly/ nå. "
                                    "Kjør tools/startpunkter.py uten --sjekk, og commit filene.")
        if bare_sjekk:
            ekstra = sorted(set(os.listdir(ARKIV)) - set(os.listdir(arkiv))) if os.path.isdir(ARKIV) else []
            feil += [f".startpunkter/{f} hører ikke til noen modul." for f in ekstra]
    # Startpunktene skal ikke forstyrre sjekken av selve specly/ (se punktum-mappen over).
    feil += sjekk("specly/", KILDE, list(kontrakter), generer=False)
    if feil:
        print("\n".join(feil))
        sys.exit(1)
    print("Alle startpunktene er gyldige" + (" og like dem i .startpunkter/." if bare_sjekk else "."))


if __name__ == "__main__":
    main()
