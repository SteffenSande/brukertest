#!/usr/bin/env python3
"""Forhåndssjekken på to nivåer: stopper FØR noe genereres eller sendes til Databricks.

  python3 tools/forhandssjekk.py <modell.json fra tools/modell.py> [<specly-mappe for nivå styring>]

Nivå «kode» (alltid, `sjekk`): det som trengs for å lage riktig kode: tabelltype, standardkolonner, datatyper, BK,
oppstrøm, relasjoner, navnestandarden, nedstrømsnavn og flagget «Eget navn», Beregning og
Radfilter.

Nivå «styring» (`sjekk_styring`): det organisasjonen krever av dokumentasjon. Det er på når prosjektet har gjort et
felt påkrevd for en tabelltype. Det er Specly sin egen innstilling (Admin → Metadatafelt → fanen «Tabelltyper»:
«Valgfri» / «Påkrevd»), som Specly skriver til `specly/Config/table_types.json` som `requiredFieldDefUuids`
(tabellfelt) og `requiredColumnFieldDefUuids` (kolonnefelt), og et felt med `isRequired` i
`metadata_field_definitions.json` («Påkrevd overalt»). Samme innstilling gir avvik i Specly og stopp her, så kravet
står ett sted. For en tabelltype med krav sjekker nivået:
  - at tabellen har en beskrivelse (den blir COMMENT i Databricks; Specly kan ikke gjøre tabellbeskrivelsen påkrevd)
  - at hvert påkrevd tabellfelt og kolonnefelt er fylt ut, og at en nedtrekksverdi finnes i listen
Et unntak Specly har lagret på tabellen (`ruleExceptions` med regelen `field.required:<nøkkel>`) respekteres.

Finner den noe, skriver den én norsk linje per problem (tabell, hva som er galt, hva du gjør i Specly) og
avslutter med kode 1. Den lager ingen kode og endrer ingenting.
"""
import glob
import json
import os
import re
import sys

TYPER = ["raw", "bronze", "sølv", "gull dimensjon", "gull fakta"]
OVER_BRONZE = ("sølv", "gull dimensjon", "gull fakta")
PREFIKS = {"raw": "raw__", "bronze": "brz__", "sølv": "slv__", "gull dimensjon": "gld__d__", "gull fakta": "gld__f__"}
RENSING = ["trim", "tom_til_null", "fjern_ledende_nuller", "store_bokstaver", "ja_nei_til_boolsk"]
TYPE_MED_FORMAT = {"date": "datoformat", "timestamp": "tidsformat"}
HELTALL = ("int", "bigint")
FAKTATYPER = ("Transaksjon", "Periodisk øyeblikksbilde")
# Navnene SCD2-dimensjonen har for gyldighet (maler/pyspark/plattform.j2: dim_fra, dim_til).
DIM_GYLDIGHET = ("gyldig_fra", "gyldig_til")
SQL_ORD = {"and", "or", "not", "null", "true", "false", "is", "in", "case", "when", "then", "else", "end", "as",
           "between", "like", "cast", "date", "timestamp", "interval", "distinct", "string", "int", "bigint",
           "decimal", "double", "boolean"}
GYLDIG_NAVN = re.compile(r"^[a-z][a-z0-9_]*$")


def navn_i_sql(sql):
    """Ordene i et SQL-uttrykk som kan være kolonnenavn (ikke tall, strenger, funksjonskall eller SQL-ord),
    med tabellprefiks der det står: [(tabell eller None, navn)]."""
    uten_strenger = re.sub(r"'[^']*'", " ", sql or "")
    funn = re.findall(r"`?([A-Za-z_][A-Za-z0-9_]*)`?(?:\s*\.\s*`?([A-Za-z_][A-Za-z0-9_]*)`?)?(\s*\()?", uten_strenger)
    ut = []
    for a, b, funksjon in funn:
        if funksjon and not b:
            continue  # funksjonskall: to_date( … )
        if b:
            ut.append((a, b))
        elif a.lower() not in SQL_ORD:
            ut.append((None, a))
    return ut


def navnet_krever_type(navn):
    """Navnestandarden gir typen: beløp er decimal, dato er date, er_/har_ er boolean osv."""
    return navn == "belop" or navn.endswith(("_belop", "_dato", "_tidspunkt")) or navn.startswith(("er_", "har_"))


def er_nokkelhash(c):
    """fb__/fk__: kolonnen har en relasjon til en annen tabells bk__ eller pk__."""
    return any(r.rsplit(".", 1)[-1].startswith(("bk__", "pk__")) for r in c["rel"])


def sjekk(m):
    feil = []
    T, K = m["tabeller"], m["kolonne"]

    def f(tabell, hva, gjor):
        feil.append(f"{tabell}: {hva} I Specly: {gjor}")

    for t in T.values():
        n, typ, kol = t["navn"], t["type"], t["kolonner"]
        if typ not in TYPER:
            f(n, f"Tabellen har tabelltype «{typ or 'ingen'}», og malene kjenner bare {', '.join(TYPER)}.", "velg tabelltype på tabellen.")
            continue
        navn = [c["navn"] for c in kol]
        std = set(t["standard"])
        data = [c for c in kol if c["navn"] not in std]
        if not n.startswith(PREFIKS[typ]):
            f(n, f"Tabellnavnet starter ikke med {PREFIKS[typ]}, som tabelltypen {typ} krever.", f"gi tabellen et navn som starter med {PREFIKS[typ]}.")
        if not GYLDIG_NAVN.match(n):
            f(n, "Tabellnavnet har andre tegn enn små bokstaver, tall og understrek.", "gi tabellen et navn med bare a-z, 0-9 og _.")
        if len(set(navn)) != len(navn):
            dobbel = sorted({x for x in navn if navn.count(x) > 1})
            f(n, f"Kolonnenavnet {', '.join(dobbel)} står flere ganger.", "gi kolonnene ulike navn.")

        # standardkolonner (columnTemplates i Config) og datatyper
        for s in t["standard"]:
            if s not in navn:
                f(n, f"Standardkolonnen {s} for tabelltypen {typ} mangler.", "trykk «Opprett manglende» på tabellen (lager standardkolonnene som mangler).")
        for c in kol:
            if not c["type"]:
                f(n, f"Kolonnen {c['navn']} har ingen datatype.", "velg datatype på kolonnen.")
            elif c["type"] not in m["datatyper"]:
                f(n, f"Kolonnen {c['navn']} har datatypen «{c['type']}», som ikke finnes i datatypene.", "velg en datatype fra listen.")
            if c["bk"] and c["navn"].startswith(("bk__", "pk__")):
                f(n, f"Kolonnen {c['navn']} har BK-flagget. BK står på de naturlige nøkkelkolonnene, aldri på bk__ eller pk__.",
                  f"ta BK-flagget av {c['navn']} og sett det på kolonnene som sammen gjør raden unik.")
            for r in c["rensing"]:
                if r not in RENSING:
                    f(n, f"Kolonnen {c['navn']} har rensingen «{r}», som koden ikke kjenner ({', '.join(RENSING)}).", "velg rensing fra listen.")
            if c["rensing"] and typ != "bronze":
                f(n, f"Kolonnen {c['navn']} har Rensing, men rensing gjøres bare i bronze.", "flytt rensingen til bronze-kolonnen.")
        for c in data:
            if c["navn"].startswith(("bk__", "pk__")):
                f(n, f"Kolonnen {c['navn']} heter som en nøkkel, men er ikke standardkolonnen {'bk__' if c['navn'].startswith('bk__') else 'pk__'}{n}. "
                     "bk__ og pk__ regnes av koden.", "gi kolonnen et annet navn, eller bruk standardkolonnen.")

        # navnestandarden fra sølv og opp; standardkolonnene unntatt
        if typ in OVER_BRONZE:
            for c in data:
                cn, ct = c["navn"], (c["type"] or "").lower()
                if not GYLDIG_NAVN.match(cn):
                    f(n, f"Kolonnen {cn} har andre tegn enn små bokstaver, tall og understrek (ingen æ, ø, å).",
                      "gi kolonnen et navn med bare a-z, 0-9 og _ (sett nedstrømsnavnet i laget før).")
                    continue
                if cn.startswith("sys__"):
                    f(n, f"Kolonnen {cn} starter med sys__, som er forbeholdt systemkolonnene tabelltypen gir.", "gi kolonnen et annet navn.")
                if cn in DIM_GYLDIGHET or not ct:
                    continue
                boolsk = cn.startswith(("er_", "har_"))
                if ct == "boolean" and not boolsk:
                    f(n, f"Kolonnen {cn} er boolean, men navnet starter ikke med er_ eller har_.", "gi kolonnen et navn som starter med er_ eller har_.")
                if boolsk and ct != "boolean":
                    f(n, f"Kolonnen {cn} starter med {cn.split('_')[0]}_, men har datatypen {c['type']}, ikke boolean.", "sett datatypen til boolean, eller gi kolonnen et annet navn.")
                if ct == "date" and not (cn == "dato" or cn.endswith("_dato")):
                    f(n, f"Kolonnen {cn} er date, men navnet slutter ikke på _dato.", "gi kolonnen et navn som slutter på _dato (for eksempel salg_dato for datoen et salg skjedde).")
                if cn.endswith("_dato") and ct != "date" and not er_nokkelhash(c) and not cn.startswith(("fb__", "fk__")):
                    f(n, f"Kolonnen {cn} slutter på _dato, men har datatypen {c['type']}, ikke date.", "sett datatypen til date.")
                if ct == "timestamp" and not cn.endswith("_tidspunkt"):
                    f(n, f"Kolonnen {cn} er timestamp, men navnet slutter ikke på _tidspunkt.", "gi kolonnen et navn som slutter på _tidspunkt.")
                if (cn == "belop" or cn.endswith("_belop")) and not ct.startswith("decimal"):
                    f(n, f"Kolonnen {cn} er et beløp, men har datatypen {c['type']}, ikke decimal.", "sett datatypen til decimal(10,2).")
                if (cn == "antall" or cn.startswith("antall_")) and ct not in HELTALL:
                    f(n, f"Kolonnen {cn} er et antall, men har datatypen {c['type']}, ikke et heltall.", "sett datatypen til int eller bigint.")
                # fb__/fk__ har hele tabellnavnet de peker på
                for pre, mal, hvor in (("fb__", "bk__", "sølv"), ("fk__", "pk__", "gull")):
                    if not cn.startswith(pre):
                        continue
                    mal_tabell = cn[len(pre):]
                    riktig = f"{mal_tabell}.{mal}{mal_tabell}"
                    if not c["rel"]:
                        f(n, f"Kolonnen {cn} er en koblingsnøkkel, men har ingen relasjon, så koden vet ikke hva den peker på.",
                          f"lag relasjonen fra {cn} til {riktig}.")
                    elif riktig not in c["rel"]:
                        f(n, f"Kolonnen {cn} peker på {', '.join(c['rel'])}. Et {pre} har hele navnet på tabellen det peker på, og peker på dens {mal}.",
                          f"gi kolonnen navnet {pre}{c['rel'][0].rsplit('.', 1)[0]}, eller la relasjonen gå til {riktig}.")
                    if pre == "fb__" and typ != "sølv":
                        f(n, f"Kolonnen {cn} er et fb__, som bare finnes i sølv. I gull peker en fk__ på en dimensjons pk__.", "bruk fk__ mot dimensjonens pk__.")
                    if pre == "fk__" and typ != "gull fakta":
                        f(n, f"Kolonnen {cn} er et fk__, som bare finnes i gull fakta.", "bruk fb__ mot en sølvtabells bk__ i sølv.")
                if er_nokkelhash(c) and not cn.startswith(("fb__", "fk__")):
                    f(n, f"Kolonnen {cn} har en relasjon til {c['rel'][0]}, men heter ikke fb__ eller fk__.",
                      f"gi kolonnen navnet {'fb__' if typ == 'sølv' else 'fk__'}{c['rel'][0].rsplit('.', 1)[0]}.")

        # BK
        bk = [c for c in kol if c["bk"]]
        if typ != "raw" and not bk:
            f(n, "Tabellen har ingen kolonne med BK-flagg, så nøkkelen (bk__/pk__) kan ikke regnes ut.", "sett BK-flagget på de naturlige nøkkelkolonnene.")

        # oppstrøm og relasjoner peker på noe som finnes
        for c in kol:
            for o in c["opp"]:
                if o not in K:
                    f(n, f"Kolonnen {c['navn']} har oppstrømskolonnen {o}, som ikke finnes.", "rett oppstrømskolonnen.")
            for r in c["rel"]:
                if r not in K:
                    f(n, f"Kolonnen {c['navn']} har en relasjon til {r}, som ikke finnes.", "rett relasjonen.")
        for tb in t["oppstromstabeller"]:
            if tb not in T:
                f(n, f"Oppstrømstabellen {tb} finnes ikke.", "rett oppstrømstabellene.")
        for r in m["relasjoner"]:
            if r["fra"] and r["fra"][0].rsplit(".", 1)[0] == n:
                for ref in r["fra"] + r["til"]:
                    if ref not in K:
                        f(n, f"Relasjonen {', '.join(r['fra'])} → {', '.join(r['til'])} nevner {ref}, som ikke finnes.", "rett relasjonen.")

        ks = m["kildesystemer"].get(t["kildesystem"]) if t["kildesystem"] else None
        if typ in ("raw", "bronze"):
            if not t["kildesystem"]:
                f(n, "Tabellen har ikke kildesystem, så koden vet ikke filformat og tekstformat.", "gi tabellen et kildesystem under «Kildesystemer» (modul 2, steg 4).")
            elif ks is None:
                f(n, f"Kildesystemet «{t['kildesystem']}» finnes ikke i kildesystemene.", "velg et kildesystem fra listen.")
            elif not ks.get("uttrekk") and typ == "bronze":
                f(n, f"Kildesystemet {t['kildesystem']} har ikke Uttrekk (Fullt eller Endringer), så historikken vet ikke om en rad som mangler er borte.",
                  f"fyll ut Uttrekk på kildesystemet {t['kildesystem']}.")
        if typ == "raw":
            if len(n.split("__")) != 3:
                f(n, "Navnet følger ikke mønsteret raw__<kilde>__<objekt>, så koden finner ikke filene i landing.", "gi tabellen riktig navn.")
            if ks is not None:
                if ks.get("filformat") not in ("csv", "json", "parquet"):
                    f(n, f"Kildesystemet {t['kildesystem']} har ikke filformat (csv, json eller parquet).", "fyll ut Filformat på kildesystemet.")
                if ks.get("filformat") == "csv" and not ks.get("skilletegn"):
                    f(n, f"Kildesystemet {t['kildesystem']} leverer CSV, men har ikke skilletegn.", "fyll ut Skilletegn på kildesystemet.")

        if typ == "bronze":
            raws = set()
            for c in data:
                if len(c["opp"]) != 1:
                    f(n, f"Kolonnen {c['navn']} må ha nøyaktig én oppstrømskolonne i raw (har {len(c['opp'])}).", "sett oppstrømskolonnen.")
                    continue
                src = K.get(c["opp"][0])
                if not src:
                    continue
                raws.add(src["tabell"])
                if T[src["tabell"]]["type"] != "raw":
                    f(n, f"Kolonnen {c['navn']} har oppstrøm {c['opp'][0]}, som ikke er en raw-tabell.", "sett oppstrømskolonnen til raw-kolonnen.")
                if c["navn"] != src["navn"]:
                    f(n, f"Kolonnen {c['navn']} heter ikke det samme som raw-kolonnen {src['navn']}. Bronze beholder kildens navn; det nye navnet er nedstrømsnavnet.",
                      f"gi kolonnen navnet {src['navn']}, og skriv {c['navn']} som nedstrømsnavn.")
                if c["beregning"]:
                    f(n, f"Kolonnen {c['navn']} har Beregning, men bronze renser bare og setter typer.", "flytt beregningen til sølv.")
                # formatet trengs bare når raw-verdien er tekst
                if ks is not None and c["type"] and src["type"] and c["type"].lower() != src["type"].lower() and src["type"].lower() == "string":
                    felt = TYPE_MED_FORMAT.get(c["type"].lower()) or ("desimaltegn" if c["type"].lower().startswith("decimal") else None)
                    if felt and not ks.get(felt):
                        f(n, f"Kolonnen {c['navn']} skal gjøres om fra {src['type']} til {c['type']}, men kildesystemet {t['kildesystem']} har ikke {felt}.",
                          f"fyll ut {felt.capitalize()} på kildesystemet {t['kildesystem']}.")
                if (c["type"] or "").lower() == "boolean" and (src["type"] or "").lower() == "string" and "ja_nei_til_boolsk" not in c["rensing"]:
                    f(n, f"Kolonnen {c['navn']} er boolean, men raw-kolonnen er tekst, og koden vet ikke hvilke verdier som er sann.", "velg rensingen ja_nei_til_boolsk.")
            if len(raws) > 1:
                f(n, f"Kolonnene har oppstrøm i flere raw-tabeller ({', '.join(sorted(raws))}); bronze leser fra én.", "sett alle oppstrømskolonnene til samme raw-tabell.")

        if t.get("union") and typ != "sølv":
            f(n, "Tabellen har «Union av», men union finnes bare i sølv.", "ta bort «Union av».")
        if typ in OVER_BRONZE:
            if bk and not bk[0]["opp"]:
                f(n, f"BK-kolonnen {bk[0]['navn']} har ingen oppstrømskolonne, så hovedtabellen kan ikke utledes.", "sett oppstrømskolonnen.")
                continue
            hoved = K[bk[0]["opp"][0]]["tabell"] if bk and bk[0]["opp"][0] in K else None
            if not hoved:
                continue
            egne = set(navn)
            # Union (feltet «Union av»): én gren per tabell i feltet.
            unionen = [x for x in t.get("union") or [] if x in T] if typ == "sølv" else []
            if typ == "sølv":
                for x in t.get("union") or []:
                    if x not in T:
                        f(n, f"«Union av» nevner {x}, som ikke finnes.", "rett «Union av».")
                if len(t.get("union") or []) == 1:
                    f(n, "«Union av» har bare én tabell. En union stabler radene fra minst to tabeller.", "legg til den andre tabellen, eller ta bort «Union av».")
                if unionen and hoved not in unionen:
                    f(n, f"BK-kolonnen {bk[0]['navn']} har oppstrøm i {hoved}, som ikke er en av tabellene i «Union av» ({', '.join(unionen)}).",
                      "la den første BK-kolonnen ha oppstrøm i en av tabellene i «Union av».")
                if unionen and t["radfilter"]:
                    f(n, "Tabellen har både «Union av» og Radfilter. Radfilter i en union støttes ikke av malene.", "ta bort Radfilter, eller filtrer i bronze.")

            def grenene(tb):
                """Grenene i unionen en oppstrømstabell hører til: seg selv, eller tabellene den har relasjon til."""
                if tb in unionen:
                    return [tb]
                return [g for g in unionen if any({r["fra"][0].rsplit(".", 1)[0], r["til"][0].rsplit(".", 1)[0]} == {g, tb} for r in m["relasjoner"])]

            def forverdi(c):
                """I en union kan Beregning bruke kolonnens egen verdi: verdien fra grenene, før Beregning."""
                return bool(unionen and c["beregning"] and any(tb is None and nv == c["navn"] for tb, nv in navn_i_sql(c["beregning"])))

            def navn_og_type(c, o):
                src = K[o]
                # nedstrømsnavnet: navnet bestemmes ett sted, som nedstrømsnavn i laget før
                forventet = src["ned"] or src["navn"]
                if c["navn"] != forventet and not c["eget_navn"]:
                    f(n, f"Kolonnen {c['navn']} har oppstrøm {o}, som har nedstrømsnavnet «{forventet}». En kolonne heter det samme som nedstrømsnavnet, "
                         f"ellers synes ikke en glemt omdøping.",
                      f"gi kolonnen navnet {forventet}, rett nedstrømsnavnet på {o}, eller sett flagget «Eget navn» på {c['navn']} når navnet skal avvike med vilje.")
                # typen: cast hører hjemme i bronze
                if c["type"] and src["type"] and c["type"].lower() != src["type"].lower():
                    f(n, f"Kolonnen {c['navn']} har datatypen {c['type']}, men oppstrømskolonnen {o} har {src['type']}. Over bronze har en kopi samme type som oppstrømmen; typen settes i bronze.",
                      "endre typen i bronze." if navnet_krever_type(c["navn"]) else
                      f"sett datatypen på {c['navn']} til {src['type']}, eller endre typen i bronze.")

            for c in data:
                if c["beregning"] and not forverdi(c):
                    continue
                if unionen:
                    if c["navn"].startswith(("fb__", "fk__")) and not c["rel"]:
                        continue
                    per_gren = {}
                    for o in c["opp"]:
                        gr = grenene(o.rsplit(".", 1)[0])
                        if len(gr) == 1:
                            per_gren.setdefault(gr[0], []).append(o)
                    for g, opp in per_gren.items():
                        if len(opp) > 1 and not er_nokkelhash(c):
                            f(n, f"Kolonnen {c['navn']} har {len(opp)} oppstrømskolonner i grenen {g} av unionen ({', '.join(opp)}). I en union har en kolonne én oppstrømskolonne per gren.",
                              "behold én oppstrømskolonne per gren, eller skriv en Beregning.")
                        elif len(opp) == 1 and not er_nokkelhash(c) and opp[0] in K:
                            navn_og_type(c, opp[0])
                    if not c["opp"] and not c["beregning"]:
                        f(n, f"Kolonnen {c['navn']} har ingen oppstrømskolonne, så koden vet ikke hvor verdien kommer fra.", "sett oppstrømskolonnen(e), eller skriv en Beregning.")
                    continue
                if not c["opp"]:
                    f(n, f"Kolonnen {c['navn']} har ingen oppstrømskolonne, så koden vet ikke hvor verdien kommer fra.", "sett oppstrømskolonnen(e), eller skriv en Beregning.")
                    continue
                if len(c["opp"]) > 1 and not er_nokkelhash(c):
                    f(n, f"Kolonnen {c['navn']} har {len(c['opp'])} oppstrømskolonner, men ingen Beregning, så koden vet ikke hvordan de skal kombineres.",
                      "skriv Beregning på kolonnen (f.eks. coalesce(a, b)), og forklaringen i Utviklernotat.")
                if c["navn"].startswith(("fb__", "fk__")) and not c["rel"]:
                    continue  # meldingen om manglende relasjon er nok; navn og type gir bare villedende råd her
                if len(c["opp"]) != 1 or er_nokkelhash(c) or c["opp"][0] not in K:
                    continue
                navn_og_type(c, c["opp"][0])
            # Beregning: over tabellens egne kolonnenavn, med utviklernotat
            for c in data:
                if not c["beregning"]:
                    continue
                for tb, nv in navn_i_sql(c["beregning"]):
                    if tb is not None:
                        f(n, f"Beregningen på {c['navn']} («{c['beregning']}») bruker {tb}.{nv}. Beregning skrives med kolonnenavnene i tabellen selv, uten tabellnavn.",
                          f"skriv {nv} i stedet for {tb}.{nv}, og sørg for at {nv} er en kolonne i {n}.")
                    elif (nv == c["navn"] and not (unionen and c["opp"])) or nv not in egne:
                        f(n, f"Beregningen på {c['navn']} («{c['beregning']}») bruker «{nv}», som ikke er en annen kolonne i {n}.",
                          f"rett Beregning, eller legg til kolonnen {nv} (med oppstrøm) i tabellen.")
                if not c["notat_utfylt"]:
                    f(n, f"Kolonnen {c['navn']} har Beregning, men ingen Utviklernotat som forklarer den for mennesker.",
                      "skriv forklaringen i Utviklernotat på kolonnen (koden leser det aldri).")
            # andre oppstrømstabeller enn hovedtabellen
            andre = []
            for c in data:
                if c["beregning"] and not forverdi(c):
                    continue
                for o in c["opp"]:
                    tb = o.rsplit(".", 1)[0]
                    if tb != hoved and tb not in unionen and tb not in andre and tb in T:
                        andre.append(tb)
            for tb in t["oppstromstabeller"]:
                if tb != hoved and tb not in unionen and tb not in andre and tb in T:
                    andre.append(tb)
            if unionen:
                for tb in andre:
                    gr = grenene(tb)
                    if len(gr) != 1:
                        f(n, f"Oppstrømstabellen {tb} har relasjon til {'ingen' if not gr else str(len(gr))} av tabellene i «Union av» ({', '.join(unionen)}), så koden vet ikke hvilken gren den skal kobles til (det må være nøyaktig én).",
                          f"lag én relasjon mellom {tb} og den tabellen i unionen den hører til.")
            elif typ == "sølv":
                for tb in andre:
                    rel = [r for r in m["relasjoner"] if {r["fra"][0].rsplit(".", 1)[0], r["til"][0].rsplit(".", 1)[0]} == {hoved, tb}]
                    if len(rel) != 1:
                        # Henter en kolonne verdien fra begge tabellene, er det trolig en union.
                        union = any({o.rsplit(".", 1)[0] for o in c["opp"]} >= {hoved, tb} for c in data if not c["beregning"] and not er_nokkelhash(c))
                        f(n, f"Oppstrømstabellen {tb} har {'ingen' if not rel else str(len(rel))} relasjon{'er' if len(rel) > 1 else ''} til hovedtabellen {hoved}, så koden vet ikke hvordan de skal kobles (det må være nøyaktig én).",
                          f"lag én relasjon mellom {tb} og {hoved} (kolonnene som skal være like)."
                          + (f" Skal radene fra {tb} komme i tillegg til radene fra {hoved}, er tabellen en union: velg begge i «Union av»." if union else ""))
            if typ == "gull dimensjon":
                for tb in andre:
                    fb = [hk["navn"] for hk in T[hoved]["kolonner"] if f"{tb}.bk__{tb}" in hk["rel"]]
                    if len(fb) != 1:
                        f(n, f"Tabellen henter kolonner fra {tb}, men hovedtabellen {hoved} har {'ingen' if not fb else str(len(fb))} fb__-kolonne{'r' if len(fb) > 1 else ''} med relasjon til {tb}.bk__{tb}, så koden vet ikke hvilken rad som hører til.",
                          f"lag fb__{tb} i {hoved} med relasjon til {tb}.bk__{tb}, eller hent kolonnen fra {hoved}.")
                for c in data:
                    if c["beregning"]:
                        f(n, f"Kolonnen {c['navn']} har Beregning, men en dimensjon kopierer bare fra sølv.", "flytt beregningen til sølv.")
            if typ == "gull fakta":
                oyeblikk = t.get("faktatype") == "Periodisk øyeblikksbilde"
                if t.get("faktatype") and t["faktatype"] not in FAKTATYPER:
                    f(n, f"Faktatype er «{t['faktatype']}», og malene kjenner bare {' og '.join(FAKTATYPER)}.", "velg Faktatype fra listen.")
                if oyeblikk:
                    # Periodisk øyeblikksbilde: dagene kommer fra én kalendertabell, med én BK-kolonne av typen date.
                    if len(andre) != 1:
                        f(n, f"Faktaen er et periodisk øyeblikksbilde, og henter dagene fra én kalendertabell ved siden av {hoved}. Den henter fra {len(andre)} andre tabeller ({', '.join(andre) or 'ingen'}).",
                          f"gi faktaen en BK-kolonne av typen date med oppstrøm i kalenderen (for eksempel slv__dato.dato), og hent resten fra {hoved}.")
                    else:
                        kal = andre[0]
                        dag = [c for c in T[kal]["kolonner"] if c["bk"]]
                        if len(dag) != 1 or (dag[0]["type"] or "").lower() != "date":
                            f(n, f"Faktaen er et periodisk øyeblikksbilde med dagene fra {kal}, men {kal} har ikke nøyaktig én BK-kolonne av typen date.", f"hent dagene fra kalenderen (slv__dato.dato).")
                        else:
                            dag = f"{kal}.{dag[0]['navn']}"
                            if not any(c["bk"] and c["opp"] == [dag] for c in data):
                                f(n, f"Faktaen er et periodisk øyeblikksbilde, men ingen BK-kolonne har oppstrøm {dag}, dagen raden gjelder.", f"legg til en BK-kolonne av typen date med oppstrøm {dag}.")
                            for c in data:
                                for o in c["opp"]:
                                    if o.rsplit(".", 1)[0] == kal and o != dag:
                                        f(n, f"Kolonnen {c['navn']} henter {o} fra kalenderen. Et periodisk øyeblikksbilde henter bare dagen ({dag}) derfra; resten kommer via fk__gld__d__dato.",
                                          f"sett oppstrømmen til {dag}, eller ta kolonnen bort.")
                for tb in ([] if oyeblikk else andre):
                    f(n, f"Faktaen henter kolonner fra {tb}, en annen tabell enn hovedtabellen {hoved}. Beskrivende kolonner fra en annen tabell hentes via en dimensjon (fk__).",
                      f"hent kolonnen fra {hoved}, eller via fk__ mot en dimensjon.")
            # Radfilter: hvert navn må finnes i en oppstrømstabell
            if t["radfilter"]:
                for tb, nv in navn_i_sql(t["radfilter"]):
                    kandidater = [x for x in [hoved] + andre if f"{x}.{nv}" in K] if tb is None else ([tb] if tb in [hoved] + andre and f"{tb}.{nv}" in K else [])
                    if not kandidater:
                        f(n, f"Radfilteret («{t['radfilter']}») bruker {tb + '.' if tb else ''}{nv}, som ikke finnes i oppstrømstabellene ({', '.join([hoved] + andre)}).", "rett Radfilter.")
                    elif len(kandidater) > 1:
                        f(n, f"Radfilteret («{t['radfilter']}») bruker {nv}, som finnes i flere oppstrømstabeller ({', '.join(kandidater)}).", f"skriv tabellnavnet foran (f.eks. {kandidater[0]}.{nv}).")

        if typ == "gull dimensjon":
            if t["historikk"] not in ("SCD1", "SCD2"):
                f(n, "Gull-dimensjonen har ikke feltet Historikk (SCD1 eller SCD2).", "velg Historikk på tabellen.")
            if t["historikk"] == "SCD2":
                for g in DIM_GYLDIGHET:
                    if g not in navn:
                        f(n, f"Dimensjonen er SCD2, men har ikke kolonnen {g}.", f"legg til {g} (timestamp) med oppstrøm sys__{g} i sølv.")
        if typ == "gull fakta":
            for c in data:
                for r in c["rel"]:
                    tt, tk = r.rsplit(".", 1)
                    dim = T.get(tt)
                    if not dim:
                        continue
                    if dim["type"] != "gull dimensjon" or tk != f"pk__{tt}":
                        f(n, f"Kolonnen {c['navn']} har en relasjon til {r}. I gull fakta peker en relasjon på en gull-dimensjons pk__.", "rett relasjonen.")
                    elif dim["historikk"] == "SCD2":
                        if not c["datoeffektiv"]:
                            f(n, f"Kolonnen {c['navn']} peker på SCD2-dimensjonen {tt}, men har ikke «Datoeffektiv på», så koden vet ikke hvilken versjon den skal velge.",
                              "velg datokolonnen i «Datoeffektiv på» på kolonnen.")
                        elif c["datoeffektiv"] not in navn:
                            f(n, f"«Datoeffektiv på» på {c['navn']} er {c['datoeffektiv']}, som ikke er en kolonne i tabellen.", "velg en datokolonne i tabellen.")
    return feil


# ── Nivå «styring» ──────────────────────────────────────────────────────────

# Innebygde kolonnefelt: verdien står alltid her i kontrakten, uansett odcsTarget i feltdefinisjonen (specly/AGENTS.md,
# «Built-in column fields»). Utviklernotatet følger builtinFieldMappings i odcs.json.
INNEBYGD_KOLONNEFELT = {"description": "description"}
MAKS_NAVN = 8


def _les_json(sti, standard):
    return json.load(open(sti, encoding="utf-8")) if os.path.exists(sti) else standard


def _camel(key):
    deler = key.split("_")
    return deler[0] + "".join(d[:1].upper() + d[1:] for d in deler[1:])


def _hent(obj, sti):
    """obj["team"]["name"] for sti «team.name»; None når et ledd mangler."""
    for ledd in sti.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(ledd)
    return obj


def _cp(obj):
    return {c.get("property"): c.get("value") for c in (obj.get("customProperties") or []) if isinstance(c, dict)}


def _utfylt(v):
    if v is None:
        return False
    if isinstance(v, (list, tuple)):
        return any(_utfylt(x) for x in v)
    return bool(str(v).strip())


def styringskrav(rot):
    """Hva hver tabelltype krever, fra specly/Config: {tabelltype: {"tabell": [felt], "kolonne": [felt]}}, der felt er
    feltdefinisjonen (dict med key, label, odcsTarget …). Tom når nivået ikke er slått på."""
    cfg = os.path.join(rot, "Config")
    defs = _les_json(os.path.join(cfg, "metadata_field_definitions.json"), [])
    etter_uuid = {d.get("uuid"): d for d in defs}
    etter_key = {d.get("key"): d for d in defs}

    def finn(ref):
        return etter_uuid.get(ref) or etter_key.get(ref)

    krav = {}
    for tt in _les_json(os.path.join(cfg, "table_types.json"), []):
        koblet_tabell = [finn(r) for r in (tt.get("metadataFieldDefUuids") or []) + (tt.get("tableFields") or [])]
        koblet_kolonne = [finn(r) for r in (tt.get("columnFieldDefUuids") or []) + (tt.get("columnFields") or [])]
        paakrevd_tabell = [finn(r) for r in tt.get("requiredFieldDefUuids") or []]
        paakrevd_kolonne = [finn(r) for r in tt.get("requiredColumnFieldDefUuids") or []]
        paakrevd_tabell += [d for d in koblet_tabell if d and d.get("isRequired")]
        paakrevd_kolonne += [d for d in koblet_kolonne if d and d.get("isRequired")]

        def unike(felt):
            sett, ut = set(), []
            for d in felt:
                if d and d.get("key") not in sett:
                    sett.add(d.get("key"))
                    ut.append(d)
            return ut

        t, k = unike(paakrevd_tabell), unike(paakrevd_kolonne)
        if t or k:
            krav[tt.get("name")] = {"tabell": t, "kolonne": k}
    return krav


def _tabellfelt(doc, s, d):
    """Verdien av et tabellfelt der feltdefinisjonen sier at det skrives (odcsTarget)."""
    mal = d.get("odcsTarget") or "customProperties"
    if mal == "customProperties":
        return _cp(s).get(d.get("odcsPropertyName") or _camel(d["key"]))
    v = _hent(s, mal)
    return v if v is not None else _hent(doc, mal)  # rotfelt som team.name og domain står på dokumentet


def _kolonnefelt(p, d):
    if d["key"] in INNEBYGD_KOLONNEFELT:
        return p.get(INNEBYGD_KOLONNEFELT[d["key"]])
    mal = d.get("odcsTarget") or "customProperties"
    if mal == "customProperties":
        return _cp(p).get(d.get("odcsPropertyName") or _camel(d["key"]))
    return _hent(p, mal)


def _unntatt(s, regel):
    for u in _cp(s).get("ruleExceptions") or []:
        r = (u or {}).get("rule", "") if isinstance(u, dict) else ""
        if r == regel or (r.endswith("*") and regel.startswith(r[:-1])):
            return True
    return False


def _navneliste(navn):
    if len(navn) <= MAKS_NAVN:
        return ", ".join(navn)
    return f"{', '.join(navn[:MAKS_NAVN])} og {len(navn) - MAKS_NAVN} til"


def sjekk_styring(rot):
    """Nivå «styring» for kontraktene under rot (specly/). Gir (på, feil): på er False når ingen tabelltype har krav."""
    import yaml  # bare her: nivå «kode» trenger ikke PyYAML

    krav = styringskrav(rot)
    if not krav:
        return False, []
    feil = []

    def f(tabell, hva, gjor):
        feil.append(f"{tabell}: {hva} I Specly: {gjor}")

    for fil in sorted(glob.glob(os.path.join(rot, "Tables", "**", "*.odcs.yaml"), recursive=True)):
        doc = yaml.safe_load(open(fil, encoding="utf-8")) or {}
        s = (doc.get("schema") or [{}])[0]
        n = s.get("name") or doc.get("name")
        typ = _cp(s).get("tableType")
        if typ not in krav:
            continue
        if not _utfylt(s.get("description")):
            f(n, f"Tabellen har ingen beskrivelse, så den får ingen COMMENT i Databricks (styring for tabelltypen {typ}).",
              "skriv beskrivelsen rett under tabellnavnet.")
        for d in krav[typ]["tabell"]:
            navn = d.get("label") or d["key"]
            if _unntatt(s, f"field.required:{d['key']}"):
                continue
            v = _tabellfelt(doc, s, d)
            if not _utfylt(v):
                f(n, f"Tabellen mangler {navn}, som er påkrevd for tabelltypen {typ}.",
                  f"fyll ut {navn} på tabellen («Vis mer»). For mange tabeller: «Import og eksport» → «Massekjøring» → «Fyll ut et tabellfelt».")
            elif d.get("dropdownOptions") and any(str(x) not in d["dropdownOptions"] for x in (v if isinstance(v, list) else [v])):
                f(n, f"{navn} er «{v}», som ikke er et av valgene ({', '.join(d['dropdownOptions'])}).", f"velg {navn} fra listen.")
        for d in krav[typ]["kolonne"]:
            navn = d.get("label") or d["key"]
            if _unntatt(s, f"field.required:{d['key']}"):
                continue
            mangler, ugyldig = [], []
            for p in s.get("properties") or []:
                v = _kolonnefelt(p, d)
                if not _utfylt(v):
                    mangler.append(p.get("name"))
                elif d.get("dropdownOptions") and any(str(x) not in d["dropdownOptions"] for x in (v if isinstance(v, list) else [v])):
                    ugyldig.append(f"{p.get('name')} («{v}»)")
            if mangler:
                hvem = f"Kolonnen {mangler[0]} mangler" if len(mangler) == 1 else f"{len(mangler)} kolonner mangler"
                liste = "" if len(mangler) == 1 else f": {_navneliste(mangler)}"
                hjelp = (f"fyll ut {navn} på kolonnene. Flere på én gang: hak av kolonnene, «Sett felt…» → {navn}."
                         if d.get("fieldType") == "nedtrekksmeny" and not d.get("isMultiSelect") else
                         f"fyll ut {navn} på kolonnene, eller koble kolonnene til et forretningsbegrep som har teksten (modul 9).")
                f(n, f"{hvem} {navn}, som er påkrevd for tabelltypen {typ}{liste}.", hjelp)
            if ugyldig:
                f(n, f"{navn} har en verdi som ikke er et av valgene ({', '.join(d['dropdownOptions'])}): {_navneliste(ugyldig)}.",
                  f"velg {navn} fra listen.")
    return True, feil


def meld(feil, niva="kode"):
    hva = "koden trenger" if niva == "kode" else "styringen krever"
    print()
    print(f"STOPP: kontraktene mangler noe {hva} ({len(feil)} ting). Ingenting er generert eller sendt til Databricks.")
    for linje in feil:
        print(f"  - {linje}")
    print()
    if niva == "styring":
        print("Kravene står i prosjektoppsettet: påkrevde felt per tabelltype (specly/Config/table_types.json).")
    print("Rett dette i Specly (eller i kontraktfilene), eksporter til Git, og kjør på nytt.")


def meld_styring_ok(paa):
    if paa:
        print("       Forhåndssjekk (styring): ingen mangler.")
    else:
        print("       Forhåndssjekk (styring): ikke slått på (ingen påkrevde felt på tabelltypene).")


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    feil = sjekk(json.load(open(sys.argv[1], encoding="utf-8")))
    if feil:
        meld(feil)
    paa, feil_styring = sjekk_styring(sys.argv[2]) if len(sys.argv) == 3 else (False, [])
    if feil_styring:
        meld(feil_styring, "styring")
    if feil or feil_styring:
        sys.exit(1)
    print("       Forhåndssjekk (kode): ingen mangler.")
    if len(sys.argv) == 3:
        meld_styring_ok(paa)


if __name__ == "__main__":
    main()
