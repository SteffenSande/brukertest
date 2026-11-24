"""Sammenligner kontraktene i to specly-mapper (din og fasit) og sier hva som avviker, på norsk.

Brukt av `./kurs sjekk` (tools/kurs.py) og notebooks/kurs_sjekk.py.

Det som sammenlignes, er det koden trenger (forhåndssjekkens kodenivå): tabellene, kolonnene,
datatype, PK, påkrevd, BK, flagg, nedstrømsnavn, rensing, oppstrøm, Beregning, relasjoner, tabelltype,
kildesystem, historikk, radfilter, Union av og Faktatype. Id-er, beskrivelser, utviklernotater, status og kolonnerekkefølge
sammenlignes ikke: de påvirker ikke koden, og id-ene er ulike i hvert Specly-prosjekt.

Fra modul 8 også styringen (avvik_styring): kravene på tabelltypene, eier og klassifisering, og at granularitet er
fylt ut der fasit har den (teksten sammenlignes ikke, som beskrivelsene). Og taggene i Databricks (avvik_tags).

Fra modul 9 også forretningsbegrepene (avvik_begreper): at begrepene finnes, datatypen, at de har regler, og hvilke
kolonner som er koblet. Fra modul 10 dataproduktet (avvik_dataprodukt): at det finnes, tabellene, eier, og at feltene
er fylt ut. `sjekk_modell` samler det som gjelder for en modul; ./kurs sjekk og notebooken bruker den.
"""
import glob
import json
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "databricks", "pyspark"))
from kursmoduler import BEGREPER_I_MODUL, DATAPRODUKT_I_MODUL, STYRING_I_MODUL, STYRINGSKRAV  # noqa: E402
from modell import cp_dict, feltdefinisjoner, feltleser, innebygd_leser, tabellnavn  # noqa: E402

TABELLFELT = {"tableType": "tabelltype", "sourceSystem": "kildesystem", "historikk": "historikk", "radfilter": "radfilter",
              "unionAv": "Union av", "faktatype": "Faktatype"}
KOLONNEFELT = {"physicalType": "datatype", "primaryKey": "PK", "required": "påkrevd", "businessName": "nedstrømsnavn",
               "transformLogic": "Beregning"}
KOLONNE_CP = {"businessKey": "BK", "rensing": "rensing", "datoeffektivPa": "Datoeffektiv på"}


def cp(obj):
    return {c.get("property"): c.get("value") for c in (obj.get("customProperties") or []) if isinstance(c, dict)}


def les(specly):
    """{tabell: {"felt": {...}, "kolonner": {kolonne: {...}}}} for alle kontraktene i specly/Tables."""
    tabeller = {}
    for fil in sorted(glob.glob(os.path.join(specly, "Tables", "**", "*.odcs.yaml"), recursive=True)):
        with open(fil, encoding="utf-8") as f:
            kontrakt = yaml.safe_load(f) or {}
        for s in kontrakt.get("schema") or []:
            t_cp = cp(s)
            felt = {norsk: t_cp.get(k) for k, norsk in TABELLFELT.items()}
            # «Union av» (felt av typen Tabell med flere valg) kan stå som YAML-liste eller som JSON-tekst.
            felt["Union av"] = tabellnavn(felt["Union av"]) or None
            felt["relasjoner"] = sorted(f"{r.get('from')} -> {r.get('to')}" for r in s.get("relationships") or [])
            kolonner = {}
            for p in s.get("properties") or []:
                k_cp = cp(p)
                k = {norsk: p.get(navn) for navn, norsk in KOLONNEFELT.items()}
                k.update({norsk: k_cp.get(navn) for navn, norsk in KOLONNE_CP.items()})
                k["PK"] = bool(k["PK"])
                k["påkrevd"] = bool(k["påkrevd"])
                k["BK"] = bool(k["BK"])
                k["flagg"] = sorted(p.get("tags") or [])
                k["oppstrøm"] = sorted(p.get("transformSourceObjects") or [])
                k["relasjon"] = sorted(r.get("to") for r in p.get("relationships") or [])
                if isinstance(k["rensing"], list):
                    k["rensing"] = sorted(k["rensing"])  # Rensingene gjøres alltid i fast rekkefølge, så rekkefølgen i listen betyr ingenting
                kolonner[p.get("name")] = k
            tabeller[s.get("name")] = {"felt": felt, "kolonner": kolonner}
    return tabeller


def vis(v):
    if v in (None, "", [], False):
        return "(tomt)" if v is not False else "nei"
    if v is True:
        return "ja"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def avvik(din_specly, fasit_specly):
    """Liste med norske setninger, én per avvik. Tom liste: kontraktene stemmer med fasit."""
    din, fasit = les(din_specly), les(fasit_specly)
    ut = []
    for t in sorted(set(fasit) - set(din)):
        ut.append(f"Tabellen {t} mangler (fasit har den).")
    for t in sorted(set(din) - set(fasit)):
        ut.append(f"Tabellen {t} finnes ikke i fasit for denne modulen.")
    for t in sorted(set(din) & set(fasit)):
        d, f = din[t], fasit[t]
        for felt in f["felt"]:
            if d["felt"][felt] != f["felt"][felt]:
                ut.append(f"{t}: {felt} er «{vis(d['felt'][felt])}», fasit har «{vis(f['felt'][felt])}».")
        for k in sorted(set(f["kolonner"]) - set(d["kolonner"])):
            ut.append(f"{t}: kolonnen {k} mangler.")
        for k in sorted(set(d["kolonner"]) - set(f["kolonner"])):
            ut.append(f"{t}: kolonnen {k} finnes ikke i fasit.")
        for k in sorted(set(d["kolonner"]) & set(f["kolonner"])):
            dk, fk = d["kolonner"][k], f["kolonner"][k]
            for felt in fk:
                if dk[felt] != fk[felt]:
                    ut.append(f"{t}.{k}: {felt} er «{vis(dk[felt])}», fasit har «{vis(fk[felt])}».")
    return ut


def les_styring(specly):
    """{"krav": {tabelltype: {kravnøkkel: [feltnøkler]}}, "tabeller": {tabell: {"eier", "granularitet",
    "klassifisering": {kolonne: verdi}}}}. Feltene leses der specly/Config sier at de står (odcsTarget)."""
    defs = feltdefinisjoner(specly)
    nokkel = {d.get("uuid"): k for k, d in defs.items()}
    with open(os.path.join(specly, "Config", "table_types.json"), encoding="utf-8") as f:
        krav = {tt["name"]: {k: sorted(nokkel.get(x, x) for x in tt[k]) for k in STYRINGSKRAV if tt.get(k)} for tt in json.load(f)}
    felt = feltleser(specly)
    tabeller = {}
    for fil in sorted(glob.glob(os.path.join(specly, "Tables", "**", "*.odcs.yaml"), recursive=True)):
        with open(fil, encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        s = (doc.get("schema") or [{}])[0]
        tabeller[s.get("name")] = {
            "eier": felt(s, cp_dict(s), "eier", doc),
            "granularitet": felt(s, cp_dict(s), "granularitet"),
            "klassifisering": {p.get("name"): felt(p, cp_dict(p), "klassifisering") for p in s.get("properties") or []},
        }
    return {"krav": krav, "tabeller": tabeller}


MAKS_KOLONNER = 8
KRAVNAVN = {"requiredFieldDefUuids": "påkrevde tabellfelt", "requiredColumnFieldDefUuids": "påkrevde kolonnefelt"}


def avvik_styring(din_specly, fasit_specly):
    """Styringen (modul 8) mot fasit: kravene på tabelltypene, eier, klassifisering og om granularitet er fylt ut.
    Liste med norske setninger. Tabeller og kolonner som mangler, meldes av avvik(), ikke her."""
    din, fasit = les_styring(din_specly), les_styring(fasit_specly)
    ut = []
    for tt in sorted(set(din["krav"]) | set(fasit["krav"])):
        for k in STYRINGSKRAV:
            d, f = din["krav"].get(tt, {}).get(k, []), fasit["krav"].get(tt, {}).get(k, [])
            if d != f:
                ut.append(f"Tabelltypen {tt}: {KRAVNAVN[k]} er «{vis(d)}», fasit har «{vis(f)}». Endres i «Admin» → "
                          "«Metadatafelt» → «Tabelltyper».")
    for t in sorted(set(din["tabeller"]) & set(fasit["tabeller"])):
        d, f = din["tabeller"][t], fasit["tabeller"][t]
        if d["eier"] != f["eier"]:
            ut.append(f"{t}: Eier er «{vis(d['eier'])}», fasit har «{vis(f['eier'])}».")
        if f["granularitet"] and not d["granularitet"]:
            ut.append(f"{t}: Granularitet er ikke fylt ut (fasit: «{f['granularitet']}»).")
        ulike = [f"{k} («{vis(d['klassifisering'][k])}», fasit «{vis(f['klassifisering'][k])}»)"
                 for k in sorted(set(d["klassifisering"]) & set(f["klassifisering"])) if d["klassifisering"][k] != f["klassifisering"][k]]
        if len(ulike) == 1:
            ut.append(f"{t}: Klassifisering på kolonnen {ulike[0]}.")
        elif ulike:
            vist = ", ".join(ulike[:MAKS_KOLONNER]) + (f" og {len(ulike) - MAKS_KOLONNER} til" if len(ulike) > MAKS_KOLONNER else "")
            ut.append(f"{t}: {len(ulike)} kolonner har en annen Klassifisering enn fasit: {vist}.")
    return ut


# ------------------------------------------------------------------------------------------- begreper (modul 9)
# Specly skriver ett begrep per fil, specly/Concepts/<navn>.md: YAML øverst (name, dataType, rules, columns) og
# beskrivelsen under. `columns` lister bare koblingene noen har laget eller endret: manuelle koblinger, utelatelser
# (link: excluded) og koblinger med unntak. En kobling en regel laget uten unntak, står ikke i filen. Hvilke kolonner et
# begrep er koblet til, er derfor: kolonnene reglene treffer, pluss dem som står i `columns`, minus de utelatte.
# Sammenlignes ikke: uuid, rekkefølge, teksten i beskrivelsen, hvilke unntak en kobling har («Behold» eller
# «Overskriv» er deltakerens valg), og hvordan regelen er skrevet, så lenge den treffer de samme kolonnene.
MATCHFELT = {"columnName": "Kolonnenavn", "downstreamName": "Nedstrømsnavn"}
MAKS_I_LISTE = 6


def navnenokkel(navn):
    """Navn sammenlignes uten hensyn til store og små bokstaver, mellomrom rundt, og æøå skrevet som ae, o, a."""
    n = " ".join(str(navn or "").split()).casefold()
    for fra, til in (("æ", "ae"), ("ø", "o"), ("å", "a")):
        n = n.replace(fra, til)
    return n


def tekst(v):
    return " ".join(str(v or "").split())


def les_begreper(specly):
    """{navnenøkkel: {"navn", "datatype", "nedstromsnavn", "regler", "koblinger": {sti: link}, "unntak": {sti: {felt}},
    "beskrivelse"}}."""
    begreper = {}
    for fil in sorted(glob.glob(os.path.join(specly, "Concepts", "*.md"))):
        with open(fil, encoding="utf-8") as f:
            innhold = f.read()
        deler = innhold.split("---\n", 2) if innhold.startswith("---") else ["", "", innhold]
        try:
            topp = yaml.safe_load(deler[1]) if len(deler) == 3 else {}
        except yaml.YAMLError:
            topp = {}
        topp = topp if isinstance(topp, dict) else {}
        navn = topp.get("name") or os.path.basename(fil)[:-3]
        koblinger, unntak = {}, {}
        for c in topp.get("columns") or []:
            if isinstance(c, str):
                koblinger[c] = "linked"
            elif isinstance(c, dict) and c.get("path"):
                koblinger[c["path"]] = c.get("link") or "linked"
                unntak[c["path"]] = set(c.get("exceptions") or [])
        begreper[navnenokkel(navn)] = {
            "navn": navn, "datatype": topp.get("dataType"), "nedstromsnavn": topp.get("downstreamName"),
            "regler": [r for r in topp.get("rules") or [] if isinstance(r, dict) and r.get("isActive") is not False],
            "koblinger": koblinger, "unntak": unntak, "beskrivelse": tekst(deler[-1]),
        }
    return begreper


def les_kolonner(specly):
    """{"tabell.kolonne": {"tabell", "navn", "nedstromsnavn", "beskrivelse"}} for alle kolonnene i specly/Tables."""
    innebygd = innebygd_leser(specly)
    kolonner = {}
    for fil in sorted(glob.glob(os.path.join(specly, "Tables", "**", "*.odcs.yaml"), recursive=True)):
        with open(fil, encoding="utf-8") as f:
            kontrakt = yaml.safe_load(f) or {}
        for s in kontrakt.get("schema") or []:
            for p in s.get("properties") or []:
                kolonner[f"{s.get('name')}.{p.get('name')}"] = {
                    "tabell": s.get("name"), "navn": p.get("name"),
                    "nedstromsnavn": innebygd(p, cp_dict(p), "downstreamName"), "beskrivelse": tekst(p.get("description"))}
    return kolonner


def regel_treffer(regel, kolonne):
    """Slik Specly leser en regel (specly/AGENTS.md, «How a rule matches»): mønsteret mot kolonnenavnet, eller mot
    nedstrømsnavnet når matchField er downstreamName. Uten isRegex må hele navnet være likt. Med isRegex holder et
    treff hvor som helst i navnet. tableNamePattern er et regulært uttrykk på tabellnavnet. De andre filtrene på en
    regel (tabelltype, dataprodukt, status, metadata) brukes ikke i kurset, og leses ikke her."""
    verdi = kolonne["nedstromsnavn"] if regel.get("matchField") == "downstreamName" else kolonne["navn"]
    monster = regel.get("columnNamePattern")
    if not verdi or not monster:
        return False
    try:
        if regel.get("tableNamePattern") and not re.search(regel["tableNamePattern"], kolonne["tabell"] or ""):
            return False
        return bool(re.search(monster, verdi)) if regel.get("isRegex") else monster == verdi
    except re.error:
        return False


def koblede(begrep, kolonner):
    """(koblet, fra_regel): stiene begrepet er koblet til, og dem av dem som bare en regel står bak (ikke i filen)."""
    utelatt = {sti for sti, link in begrep["koblinger"].items() if link == "excluded"}
    i_filen = {sti for sti in begrep["koblinger"] if sti in kolonner} - utelatt
    treff = {sti for sti, k in kolonner.items() if any(regel_treffer(r, k) for r in begrep["regler"])} - utelatt
    return i_filen | treff, treff - i_filen


def vis_regler(regler):
    return ", ".join(f"{MATCHFELT.get(r.get('matchField') or 'columnName', r.get('matchField'))} «{r.get('columnNamePattern')}»"
                     for r in regler)


def vis_liste(stier):
    stier = sorted(stier)
    return ", ".join(stier[:MAKS_I_LISTE]) + (f" og {len(stier) - MAKS_I_LISTE} til" if len(stier) > MAKS_I_LISTE else "")


def antall(n, en, flere):
    return f"{n} {en if n == 1 else flere}"


def avvik_begreper(din_specly, fasit_specly):
    """Forretningsbegrepene (modul 9) mot fasit. Gir (avvik, oppsummering): norske setninger, og linjen sjekken
    avslutter med. Kolonner i tabeller du ikke har, meldes av avvik(), ikke her."""
    din, fasit = les_begreper(din_specly), les_begreper(fasit_specly)
    din_kol, fasit_kol = les_kolonner(din_specly), les_kolonner(fasit_specly)
    navnene = ", ".join(b["navn"] for b in fasit.values())
    ut = []
    if fasit and not din:
        ut.append(f"Fant ingen begreper i specly/Concepts. Fasit har {len(fasit)}: {navnene}. Har du laget dem i Specly "
                  "(«Forretningsordbok»), må de eksporteres til Git («Import og eksport» → «Eksporter til Git») og hentes "
                  "hit (git pull, eller «Pull» i Git-mappen) før sjekken ser dem.")
    koblet_i_alt = 0
    for nokkel, f in fasit.items() if din else []:
        d = din.get(nokkel)
        if not d:
            ut.append(f"Begrepet {f['navn']} mangler. Lag det under «Forretningsordbok» i Specly (modul 9, steg 2 og 4), "
                      "og eksporter til Git. Navnet må være det samme som i modulteksten.")
            continue
        b = f"Begrepet {d['navn']}"
        if navnenokkel(d["datatype"]).replace(" ", "") != navnenokkel(f["datatype"]).replace(" ", ""):
            ut.append(f"{b}: datatypen er «{vis(d['datatype'])}», fasit har «{vis(f['datatype'])}».")
        if f["beskrivelse"] and not d["beskrivelse"]:
            ut.append(f"{b} har ingen forretningsbeskrivelse. Det er den teksten de koblede kolonnene arver.")
        if d["nedstromsnavn"] and not f["nedstromsnavn"]:
            ut.append(f"{b} har nedstrømsnavnet «{d['nedstromsnavn']}». Feltet skal være tomt: ellers får alle de "
                      "koblede kolonnene det navnet, og kolonnene i neste lag blir omdøpt (modul 9, steg 2).")
        if f["regler"] and not d["regler"]:
            ut.append(f"{b} har ingen regler. Fasit har {antall(len(f['regler']), 'regel', 'regler')}: "
                      f"{vis_regler(f['regler'])} (modul 9, steg 3: «Legg til regel» på begrepet).")
        d_koblet, d_regel = koblede(d, din_kol)
        f_koblet, _ = koblede(f, fasit_kol)
        felles = set(din_kol) & set(fasit_kol)
        mangler, ekstra = (f_koblet - d_koblet) & felles, (d_koblet - f_koblet) & felles
        koblet_i_alt += len(d_koblet & felles)
        if mangler:
            ut.append(f"{b}: {antall(len(mangler), 'kolonne er', 'kolonner er')} ikke koblet til begrepet: {vis_liste(mangler)}. "
                      + (f"Fasit kobler dem med reglene {vis_regler(f['regler'])}. " if f["regler"] else "")
                      + ("Du har: " + vis_regler(d["regler"]) + "." if d["regler"] else "Se modul 9, steg 3."))
        if ekstra:
            ut.append(f"{b}: {antall(len(ekstra), 'kolonne er', 'kolonner er')} koblet til begrepet, men ikke i fasit: "
                      f"{vis_liste(ekstra)}. Treffer en regel for mye? Et mønster treffer hvor som helst i navnet hvis "
                      "«Match hele navnet» ikke er haket av (modul 9, steg 3).")
        # En kobling en regel laget uten unntak, står ikke i begrepsfilen. Det som viser at regelen er brukt, er at
        # kolonnen har fått begrepets tekst. Har den en annen tekst, er regelen lagret uten at kolonnen er koblet, eller
        # begrepets tekst er endret uten at kolonnene fikk den. Filene alene sier ikke hvilken av de to.
        ikke_brukt = {sti for sti in d_regel & f_koblet & felles
                      if d["beskrivelse"] and din_kol[sti]["beskrivelse"] != d["beskrivelse"]}
        if ikke_brukt:
            ut.append(f"{b}: en regel treffer {vis_liste(ikke_brukt)}, men {'kolonnen' if len(ikke_brukt) == 1 else 'kolonnene'} "
                      "har verken begrepets beskrivelse eller et unntak i begrepsfilen. Enten er regelen lagret uten å være "
                      "brukt (trykk «Bruk alle regler» i listen over begrepene i Specly), eller så er beskrivelsen på begrepet "
                      "endret uten «Lagre og oppdater» (modul 9, steg 5). Se under «Koblede kolonner» på begrepet, og "
                      "eksporter til Git på nytt.")
        # En kobling som står i begrepsfilen uten unntak for beskrivelsen, arver også teksten. Hvilke unntak koblingen har,
        # sammenlignes ikke med fasit, men uten unntaket skal kolonnen ha begrepets tekst.
        ikke_arvet = {sti for sti in (d_koblet - d_regel) & f_koblet & felles
                      if d["beskrivelse"] and "businessDescription" not in d["unntak"].get(sti, set())
                      and din_kol[sti]["beskrivelse"] != d["beskrivelse"]}
        if ikke_arvet:
            ut.append(f"{b}: {vis_liste(ikke_arvet)} er koblet uten unntak for beskrivelsen, men har ikke begrepets tekst. "
                      "Trolig er beskrivelsen på begrepet endret uten «Lagre og oppdater» (modul 9, steg 5). Åpne begrepet i "
                      "Specly, lagre beskrivelsen på nytt med «Lagre og oppdater», og eksporter til Git.")
    if ut:
        return ut, f"{len(ut)} avvik i begrepene."
    return ut, (f"Begrepene stemmer med fasit ({antall(len(fasit), 'begrep', 'begreper')}, "
                f"{antall(koblet_i_alt, 'koblet kolonne', 'koblede kolonner')}).")


# --------------------------------------------------------------------------------------- dataprodukt (modul 10)
# Specly skriver ett dataprodukt per fil, specly/DataProducts/<navn>.odps.yaml. Tabellene (og diagrammene) står som
# navn i customProperties. Sammenlignes: at produktet finnes, tabellene (begge veier), eier, og at det som er fylt ut
# i fasit (beskrivelse, bruk, begrensninger og egne felt som Forbruker), er fylt ut hos deg. Teksten sammenlignes ikke.
# Diagrammet: har fasit et diagram, skal du ha minst ett. Id-er, status, versjon og rekkefølge sammenlignes ikke.
DP_TEKSTFELT = {"purpose": "Beskrivelse", "usage": "Bruk", "limitations": "Begrensninger"}
DP_IKKE_FELT = ("speclyId", "tables", "diagrams")


def les_dataprodukter(specly):
    """{navnenøkkel: {"navn", "fil", "tabeller", "diagrammer", "eier", "tekst": {felt: tekst}, "felt": {navn: verdi}}}."""
    produkter = {}
    for fil in sorted(glob.glob(os.path.join(specly, "DataProducts", "*.odps.yaml"))):
        with open(fil, encoding="utf-8") as f:
            try:
                doc = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                doc = {}
        doc = doc if isinstance(doc, dict) else {}
        egne = cp_dict(doc)
        navn = doc.get("name") or os.path.basename(fil)[: -len(".odps.yaml")]
        beskrivelse = doc.get("description") if isinstance(doc.get("description"), dict) else {}
        produkter[navnenokkel(navn)] = {
            "navn": navn, "fil": os.path.basename(fil),
            "tabeller": set(tabellnavn(egne.get("tables"))), "diagrammer": set(tabellnavn(egne.get("diagrams"))),
            "eier": (doc.get("team") or {}).get("name") if isinstance(doc.get("team"), dict) else None,
            "tekst": {k: tekst(beskrivelse.get(k)) for k in DP_TEKSTFELT},
            "felt": {k: v for k, v in egne.items() if k not in DP_IKKE_FELT},
        }
    return produkter


def avvik_dataprodukt(din_specly, fasit_specly):
    """Dataproduktet (modul 10) mot fasit. Gir (avvik, oppsummering), som avvik_begreper."""
    din, fasit = les_dataprodukter(din_specly), les_dataprodukter(fasit_specly)
    ut = []
    for nokkel, f in fasit.items():
        d = din.get(nokkel)
        if not d:
            har = f" Du har: {', '.join(p['navn'] for p in din.values())}." if din else ""
            ut.append(f"Dataproduktet {f['navn']} mangler: fant ikke specly/DataProducts/{f['fil']}.{har} Lag det under "
                      "«Dataprodukter» i Specly (modul 10, steg 1), eksporter til Git, og hent endringene hit (git pull, "
                      "eller «Pull» i Git-mappen).")
            continue
        p = f"Dataproduktet {d['navn']}"
        for t in sorted(f["tabeller"] - d["tabeller"]):
            ut.append(f"{p} mangler tabellen {t}. Legg den til på dataproduktet i Specly (modul 10, steg 2).")
        for t in sorted(d["tabeller"] - f["tabeller"]):
            ut.append(f"{p} har tabellen {t}, som ikke er med i fasit. Et dataprodukt er det du leverer, ikke alt det "
                      "er laget av: ta tabellen ut av dataproduktet i Specly (modul 10, steg 2).")
        if navnenokkel(d["eier"]) != navnenokkel(f["eier"]):
            ut.append(f"{p}: Eier er «{vis(d['eier'])}», fasit har «{vis(f['eier'])}» (modul 10, steg 1).")
        for felt, norsk in DP_TEKSTFELT.items():
            if f["tekst"][felt] and not d["tekst"][felt]:
                ut.append(f"{p}: {norsk} er ikke fylt ut (modul 10, steg {1 if felt == 'purpose' else 4}).")
        for felt, verdi in f["felt"].items():
            if verdi and not d["felt"].get(felt):
                ut.append(f"{p}: feltet {felt[:1].upper() + felt[1:]} er ikke fylt ut (modul 10, steg 4).")
        if f["diagrammer"] and not d["diagrammer"]:
            ut.append(f"{p} har ikke noe diagram. Legg til diagrammet {vis_liste(f['diagrammer'])} under «Diagrammer» på "
                      "dataproduktet (modul 10, steg 3).")
    if ut:
        return ut, f"{len(ut)} avvik i dataproduktet."
    hva = ", ".join(f"{p['navn']} med {antall(len(p['tabeller']), 'tabell', 'tabeller')}" for p in fasit.values())
    return ut, f"Dataproduktet stemmer med fasit ({hva})."


# ------------------------------------------------------------------------------------ det som gjelder for modulen
def hva_sjekkes(modul):
    """Setningen som sier hva modellen sammenlignes på, for overskriften i ./kurs sjekk."""
    if modul >= BEGREPER_I_MODUL:
        return ("kontraktene med styringen, forretningsbegrepene" + (" og dataproduktet" if modul >= DATAPRODUKT_I_MODUL else "")
                + "; id-er og beskrivelser teller ikke")
    return ("det koden trenger; id-er og beskrivelser teller ikke"
            + ("; fra modul 8 også kravene, eier, granularitet og klassifisering" if modul >= STYRING_I_MODUL else ""))


def sjekk_modell(din_specly, fasit_specly, modul):
    """Alt i specly/ som sammenlignes med fasit for modulen: [(hva, avvik, oppsummering)]. Kontraktene alltid (med
    styringen fra modul 8), begrepene fra modul 9 og dataproduktet fra modul 10."""
    funn = avvik(din_specly, fasit_specly) + (avvik_styring(din_specly, fasit_specly) if modul >= STYRING_I_MODUL else [])
    ut = [("kontraktene", funn, f"{len(funn)} avvik i kontraktene." if funn else "Kontraktene stemmer med fasit.")]
    if modul >= BEGREPER_I_MODUL:
        ut.append(("begrepene", *avvik_begreper(din_specly, fasit_specly)))
    if modul >= DATAPRODUKT_I_MODUL:
        ut.append(("dataproduktet", *avvik_dataprodukt(din_specly, fasit_specly)))
    return ut


def avvik_tags(sql, katalog, skjema, tags, eide):
    """Taggene i Databricks mot `tags` (det fasit gir, tools/generer.py tags_for). sql: en funksjon spørring → rader,
    eller en Spark-økt. Gir (avvik, mangler): avvik er norske setninger, én per setning sett_tags ville kjørt.
    mangler er tabellene fasit har, men som ikke finnes i skjemaet. De kan ikke ha tags, og sammenlignes ikke."""
    from plattform.tags import les_eksisterende, setninger
    finnes, typer = les_eksisterende(sql, katalog, skjema, eide)
    avvik = [f"Taggene i Databricks avviker fra fasit. Det som må til: {x}"
             for x in setninger(katalog, skjema, {t: v for t, v in tags.items() if t in typer}, eide, finnes, typer)]
    return avvik, sorted(t for t in tags if t not in typer)


def tagglinje(avvik, mangler, antall, kjor):
    """Linjen sjekken avslutter taggene med. `antall`: tabellene fasit har. `kjor`: det som setter taggene
    (./kjor eller kurs_generer_kjor)."""
    if avvik:
        return f"{len(avvik)} avvik i taggene. Kjør {kjor}, så settes de etter kontraktene."
    if mangler:
        return (f"Taggene stemmer for de {antall - len(mangler)} tabellene som finnes. {len(mangler)} av {antall} "
                "tabeller i fasit finnes ikke i skjemaet, og er ikke sjekket (se avvikene over).")
    return "Taggene stemmer med fasit."
