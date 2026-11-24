#!/usr/bin/env python3
"""Samler kryss-fakta fra alle kontraktene til én fil malene kan importere.

  uv run --no-project --with pyyaml python tools/modell.py <specly-mappe> <ut: modell.j2> [<ut: modell.json>]

`datacontract export custom` gir en mal bare ÉN kontrakt. Det malene trenger fra andre kontrakter
(oppstrømmens type og navn, relasjoner, måltabellens BK og Historikk) og fra specly/Config
(kildesystemenes format, standardkolonnene per tabelltype) står her som rene fakta.
Skriptet lager ingen kode og bestemmer ingenting: det leser og skriver ut. tools/forhandssjekk.py
bruker de samme faktaene til å stoppe før noe genereres.
"""
import glob
import json
import os
import sys

import yaml

from forhandssjekk import navn_i_sql

# Flaggene koden leser fra `tags` (navnet i specly/Config/flags.json).
FLAGG_EGET_NAVN = "Eget navn"


def cp_dict(obj):
    return {c.get("property"): c.get("value") for c in (obj.get("customProperties") or []) if isinstance(c, dict)}


def innebygd_leser(rot):
    """Gir en funksjon som leser et innebygd Specly-felt (oppstrøm, Developer Note, nedstrømsnavn …) fra der
    prosjektet har valgt å skrive det: specly/Config/odcs.json (`builtinFieldMappings`), enten som en
    customProperty (standard) eller som et eget ODCS-felt (f.eks. `transformSourceObjects`)."""
    sti = os.path.join(rot, "Config", "odcs.json")
    odcs = json.load(open(sti, encoding="utf-8")) if os.path.exists(sti) else {}
    koblinger = odcs.get("builtinFieldMappings") or {}
    # Nedstrømsnavnet er kolonnens businessName når columnBusinessNameSource er downstreamName.
    navn_fra_ned = odcs.get("columnBusinessNameSource") == "downstreamName"

    def les(obj, cp, felt):
        if felt == "downstreamName" and navn_fra_ned:
            return obj.get("businessName")
        kobling = koblinger.get(felt) or {}
        mal = kobling.get("odcsTarget") or "customProperties"
        if mal == "customProperties":
            return cp.get(kobling.get("odcsPropertyName") or felt)
        return obj.get(mal)

    return les


def feltdefinisjoner(rot):
    """{nøkkel: feltdefinisjon} fra specly/Config/metadata_field_definitions.json. Tom når filen ikke finnes."""
    sti = os.path.join(rot, "Config", "metadata_field_definitions.json")
    return {d["key"]: d for d in (json.load(open(sti, encoding="utf-8")) if os.path.exists(sti) else [])}


def feltleser(rot):
    """Gir en funksjon som leser et prosjektfelt (specly/Config/metadata_field_definitions.json) der feltet er skrevet:
    som customProperty (navnet er `odcsPropertyName`, ellers nøkkelen i camelCase) eller i ODCS-feltet `odcsTarget`.
    Et ODCS-felt med punktum leses ledd for ledd (`team.name` → team, så name). Et tabellfelt som ikke står på
    tabellobjektet, leses fra roten av dokumentet (`dok`): der står `team.name`, `domain` og `tenant`.
    Et felt prosjektet ikke har, gir None."""
    defs = feltdefinisjoner(rot)

    def camel(key):
        deler = key.split("_")
        return deler[0] + "".join(d[:1].upper() + d[1:] for d in deler[1:])

    def les(obj, cp, key, dok=None):
        d = defs.get(key) or {}
        mal = d.get("odcsTarget") or "customProperties"
        if mal == "customProperties":
            return cp.get(d.get("odcsPropertyName") or camel(key))
        v = hent(obj, mal)
        return hent(dok, mal) if v is None and dok is not None else v

    return les


def hent(obj, sti):
    """obj["team"]["name"] for stien «team.name». None når et ledd mangler."""
    for ledd in sti.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(ledd)
    return obj


def malnavn(tabelltype):
    """Malfilen for en tabelltype: «gull dimensjon» → gull_dimensjon, «sølv» → solv."""
    return (tabelltype or "").replace("ø", "o").replace("æ", "ae").replace("å", "a").replace(" ", "_")


def som_liste(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def tabellnavn(v):
    """Et felt av typen «Tabell» (Union av): en liste med tabellnavn. Med flere valg skriver Specly listen som YAML-liste
    eller som JSON-tekst («["a","b"]»); begge leses."""
    if isinstance(v, str) and v.strip().startswith("["):
        try:
            v = json.loads(v)
        except ValueError:
            pass
    return [x for x in som_liste(v) if isinstance(x, str) and x]


def last_modell(rot):
    """Leser specly/Tables/**/*.odcs.yaml og specly/Config. Gir modellen som dict."""
    tabeller, kolonne, relasjoner = {}, {}, []
    innebygd, felt = innebygd_leser(rot), feltleser(rot)
    cfg = os.path.join(rot, "Config")

    def registry(name):
        p = os.path.join(cfg, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []

    standardmaler = {tt["name"]: [c["name"] for c in tt.get("columnTemplates") or []] for tt in registry("table_types.json")}
    for fil in sorted(glob.glob(os.path.join(rot, "Tables", "**", "*.odcs.yaml"), recursive=True)):
        with open(fil, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        s = (doc.get("schema") or [{}])[0]
        tcp = cp_dict(s)
        navn = s.get("name") or doc.get("name")
        kolonner = []
        for prop in s.get("properties") or []:
            ccp = cp_dict(prop)
            rels = []
            for r in prop.get("relationships") or []:
                if r.get("type", "foreignKey") == "foreignKey" and isinstance(r.get("to"), str):
                    rels.append(r["to"])
                    relasjoner.append({"fra": [f"{navn}.{prop.get('name')}"], "til": [r["to"]]})
            tags = prop.get("tags") or []
            k = {
                "navn": prop.get("name"),
                "type": prop.get("physicalType"),
                "bk": innebygd(prop, ccp, "businessKey") is True,
                "pk": prop.get("primaryKey") is True,
                "opp": som_liste(innebygd(prop, ccp, "upstreamColumns")),
                "ned": innebygd(prop, ccp, "downstreamName"),
                "rensing": som_liste(felt(prop, ccp, "rensing")),
                "beregning": felt(prop, ccp, "beregning"),
                # Navnene Beregning bruker (uten tabellnavn). Malen for union ser her om Beregning bruker kolonnens egen verdi.
                "beregning_bruker": [nv for tb, nv in navn_i_sql(felt(prop, ccp, "beregning")) if tb is None],
                # Developer Note er for mennesker: bare OM den er utfylt kommer med, aldri teksten, så ingen mal kan lese den.
                "notat_utfylt": bool(str(innebygd(prop, ccp, "developerNote") or "").strip()),
                "datoeffektiv": felt(prop, ccp, "datoeffektiv_pa"),
                "eget_navn": FLAGG_EGET_NAVN in tags,
                # Styring (modul 8): blir kolonnetaggen klassifisering i Unity Catalog (plattform/tags.py).
                "klassifisering": felt(prop, ccp, "klassifisering"),
                "tags": tags,
                "rel": rels,
            }
            kolonner.append(k)
            kolonne[f"{navn}.{k['navn']}"] = dict(k, tabell=navn)
        # Sammensatte relasjoner (flere kolonner) står på tabellen: from/to er lister i par.
        for r in s.get("relationships") or []:
            if r.get("type", "foreignKey") == "foreignKey" and isinstance(r.get("from"), list) and isinstance(r.get("to"), list):
                relasjoner.append({"fra": list(r["from"]), "til": list(r["to"])})
        typ = innebygd(s, tcp, "tableType")
        tabeller[navn] = {
            "navn": navn,
            "fil": os.path.relpath(fil, os.path.dirname(rot)),
            "type": typ,
            "mal": malnavn(typ),
            "kildesystem": innebygd(s, tcp, "sourceSystem"),
            "historikk": felt(s, tcp, "historikk"),
            "radfilter": felt(s, tcp, "radfilter"),
            # Sølv: tabellen er en union av radene fra disse oppstrømstabellene (feltet «Union av»). Tom: ingen union.
            "union": tabellnavn(felt(s, tcp, "union_av")),
            # Gull fakta: «Transaksjon» (tomt) eller «Periodisk øyeblikksbilde» (feltet «Faktatype»).
            "faktatype": felt(s, tcp, "faktatype"),
            # Styring (modul 8): eieren (team.name på roten av dokumentet) blir tabelltaggen eier i Unity Catalog.
            "eier": felt(s, tcp, "eier", doc),
            "granularitet": felt(s, tcp, "granularitet"),
            "oppstromstabeller": som_liste(innebygd(s, tcp, "upstreamTables")),
            # Standardkolonnene tabelltypen gir (columnTemplates), med tabellens navn satt inn.
            "standard": [m.replace("{table_name}", navn) for m in standardmaler.get(typ, [])],
            "kolonner": kolonner,
        }
    kildesystemer = {k["name"]: dict(k.get("metadataValues") or {}) for k in registry("source_systems.json")}
    datatyper = [d["name"] for d in registry("datatypes.json")]
    flagg = [f["name"] for f in registry("flags.json")]
    # Valgene for Klassifisering, fra den åpneste til den strengeste. Malen for tags gir tabellen den strengeste
    # klassifiseringen blant kolonnene, i denne rekkefølgen. Tom når prosjektet ikke har feltet.
    klassifiseringer = list((feltdefinisjoner(rot).get("klassifisering") or {}).get("dropdownOptions") or [])
    return {"tabeller": tabeller, "kolonne": kolonne, "relasjoner": relasjoner, "kildesystemer": kildesystemer,
            "datatyper": datatyper, "flagg": flagg, "standardkolonner": standardmaler, "klassifiseringer": klassifiseringer}


def jinja(v):
    """Python-verdi som Jinja-literal (JSON, men none/true/false)."""
    if v is None:
        return "none"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(jinja(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{json.dumps(str(k), ensure_ascii=False)}: {jinja(x)}" for k, x in v.items()) + "}"
    raise TypeError(type(v))


def j2(m):
    """Innholdet i modell.j2: faktaene som en Jinja-variabel malene importerer."""
    return ("{#- GENERERT av tools/modell.py fra kontraktene og specly/Config. Ikke rediger. -#}\n"
            "{%- set modell = " + jinja(m) + " -%}\n")


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    m = last_modell(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write(j2(m))
    if len(sys.argv) == 4:
        with open(sys.argv[3], "w", encoding="utf-8") as fh:
            json.dump(m, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
