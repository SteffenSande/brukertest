#!/usr/bin/env python3
"""Specly-sjekken: finner det i dette repoet som Specly ikke kan lese inn.

Specly skriver denne filen. Ikke endre den: neste skriving fra Specly legger
sin egen tekst tilbake.

    uv run --no-project --with pyyaml python <denne filen> check
    uv run --no-project --with pyyaml python <denne filen> check --changed-from origin/dev
    uv run --no-project --with pyyaml python <denne filen> check --verbose
    uv run --no-project --with pyyaml python <denne filen> check --strict
    uv run --no-project --with pyyaml python <denne filen> fix
    uv run --no-project --with pyyaml python <denne filen> fix --changed-from origin/dev --dry-run

Sjekken trenger bare Python 3.9 eller nyere og pyyaml. Den snakker aldri med Specly. Alle
regler og lister leses fra filene i branchen (`.specly.json`, config-mappen
og `.specly/schemas/`), så en ny datatype eller en endret innstilling i samme
branch gjelder med en gang.

`check` går alltid gjennom hele repoet. Med `--changed-from <ref>` vises bare
funn i filer som er endret siden <ref>, og funn i filer som peker på dem. En
endret registerfil i config-mappen viser funn i andre filer bare for verdiene
endringen rører: en verdi som er tatt bort eller har fått nytt navn, vises i
hver kontrakt som fortsatt bruker den; en ny verdi viser ingenting nytt.

En feil er noe Specly ikke kan lese inn: en fil den avviser (kontrakt,
dataprodukt, diagram, begrep eller config-fil med feil form), en referanse til
noe som ikke finnes, samme uuid to steder, en tabelltype, et kildesystem, en
status eller et flagg som ikke finnes i registeret i repoet (Hent fra Git
stopper på en verdi Specly ikke har, og repoet skal ha hver verdi
kontraktene bruker). En advarsel er noe Specly leser, men ikke slik det
står: en verdi den hopper over eller leser som tom, en datatype som ikke
finnes i datatypes.json («Fra Git» ber om en type for kolonnen), en fil den
aldri leser. Kildesystemene leses der eksportoppsettet i .specly.json sier
(sourceSystemsFolder, sourceSystemsFormat: JSON eller YAML), ellers fra
source_systems.json i config-mappen.

Formatet sjekkes slik: filen leses, skrives ut slik Specly skriver den, og
sammenlignes med det som står der. Det gjelder kontrakter, dataprodukter,
begreper, diagrammer og config-filene: anførselstegn, innrykk, linjeskift
og BOM. Rekkefølgen sjekkes aldri: ikke nøklene, ikke listene (tagger,
customProperties, lenkene og nøklene i en begrepsfil). En eksport lar en fil
som er lik Specly som verdier, stå, og beholder ellers filens rekkefølge;
kolonne- og regelrekkefølge som er data, melder reglene (`rules.sort.*`).
Nøkler Specly ikke skriver øverst i en begrepsfil (`owner: team`) sjekkes ikke
heller: Specly leser dem ikke, og eksporten lar dem stå som de er.
`--no-format` slår formatsjekken av.
En fil som Specly leser, men som ikke står slik Specly skriver den, er en
advarsel (`format.differs`): Specly leser den som den står. En eksport
skriver bare feltene som er endret i Specly inn i en kontrakt, i filens egen
form og rekkefølge; heller ikke «Nytt filformat» (når en ODCS- eller
mappeinnstilling endres) skriver om en fil som er lik som verdier. En registerfil i config-mappen skrives
derimot hel, i Specly-format, av hver eksport som tar en endring i den: da
skrives hver uendret oppføring med samme uuid som i Specly slik Specly
skriver den (Speclys nøkkelrekkefølge; nøkler Specly ikke skriver, faller bort). `--strict` gjør `format.differs` til en feil.
Kildesystemene i YAML (source_systems.yaml) skriver eksporten bare oppføring for oppføring: formatsjekken ser der
bare på anførselstegnene (hver tekst i `"` med quoteAllStrings, eller når filen har hver tekst i `"`).

En verdi uten anførselstegn som Specly leser som tekst, men en YAML 1.1-leser (PyYAML) som noe annet (`Yes`,
`on`, `12:30`, `2026-11-19`, `0123`), er en feil (`yaml.ambiguousPlain`): samme fil gir to ulike data. Sjekken ser
på teksten i kildesystemene i YAML, kontraktene, dataproduktene og toppen av begrepsfilene. `fix` setter
anførselstegn rundt verdien, og endrer ikke noe annet.

Noen former leser Specly, men eksporten kan ikke skrive visse endringer i dem
og stopper (`export.refused`, en feil); meldingen sier hvilke: YAML-ankere og
henvisninger (&a, *a) stopper hver endring i filen; en tabell eller kolonne i
flytstil ({...}) en endring i dens felt; en liste med tabeller, kolonner eller
regler i flytstil, eller med `-` alene på linjen på det første elementet, et
nytt element; `description:` (eller name, physicalType, logicalType) uten noe
etter kolonet eller med en liste der, en endring av det feltet; og kildene
(transformSourceObjects, en verdi i customProperties) som en liste i flytstil
over flere linjer, å ta ut en kilde som er slettet i Specly.

En kolonne uten description er en advarsel (`lint.column.noDescription`). Slike
advarsler vises som én linje per fil med antallet, og et totalt antall til
slutt; `--verbose` viser hver kolonne. `--json` har alltid hver enkelt.

Begrepslenker (`lint.concept.*`): sjekken regner ut det «Bruk reglene» i
Specly gjør med panelets standardvalg (alle begreper, «Behold egen tekst»,
ikke «Sett datatype fra begrepet»), og melder det neste eksport da ville
endret: en lenke med unntak som mangler i begrepsfilen (`missingLink`), et
unntak Specly lager på en lenke som står der (`missingException`), tekst
Specly fyller inn fra begrepet i en tom kolonne (`inheritedText`), en
regellenke ingen regel treffer lenger (`staleRuleLink`), et begrep uten uuid
(`noUuid`). Det filene alene ikke avgjør, meldes som `undetermined`.

Reglene i config-mappen (`rules.*`): flaggregler, kolonnesorteringsregler og
relasjonsregler kjører aldri av seg selv i Specly; en bruker kjører dem. Et
`rules.*`-funn sier hva en kjøring av reglene i Specly ville endret, ikke hva
neste eksport endrer: flagg kolonnene får (`rules.flag.wouldAdd`), ny
kolonnerekkefølge (`rules.sort.wouldReorder`, regnet fra rekkefølgen i filen),
og relasjoner reglene ville laget (`rules.relation.wouldCreate`, én linje per
regel). Det filene alene ikke avgjør, meldes som `undetermined`. Funnene er
alltid advarsler; med `--changed-from` gjelder de bare det endringene kan
endre i en kjøring (kolonner og tabeller der endringene rører det reglene
leser; alle, når endringene kan gi et annet utfall av reglene: en endret regelfil
eller odcs.json, eller en endret, ny eller borte oppføring i flags.json eller
datatypes.json som en regel nevner; en ny datatype en kolonne har, under en
datatype_group-regel, gjelder den tabellen). `lineage.autoRename` (bare med `--changed-from`) melder en
kolonne med nytt navn eller nedstrømsnavn som kan omdøpe kolonnene den er
kilde til når endringen tas inn.

`fix` skriver filene i Specly-format. Med `--add-values` legger den også
datatyper, tagger, statuser, tabelltyper og kildesystemer kontraktene bruker,
men som mangler i registeret, til der, slik Specly selv skriver dem (uuid
laget av navnet). Uten flagget finner den aldri på en verdi: en skrivefeil
skal ikke bli en ny verdi. Den legger også inn det neste eksport ville skrevet etter
«Bruk reglene»: de nye lenkene i begrepsfilene, begrepets tekst i tomme
kolonner og uuid på et begrep uten, slik eksporten skriver det inn i filen.
Med `--apply-rules` gjør den i Git først det en kjøring av flaggreglene og
kolonnesorteringsreglene i Specly ville gjort (nye flagg, ny
kolonnerekkefølge), bare der utfallet er sikkert; uten flagget skriver den
ingenting for `rules.*`. Relasjoner og omdøpinger skriver den aldri.
Med `--add-ids --changed-from <ref>` gir den tabeller og kolonner som er nye
siden <ref> og mangler id, den id-en Specly selv ville gitt dem ved
innhentingen (uuid v5 i navnerommet prosjekt-id-en av kontraktens `id`,
tabellnavnet og kolonnenavnet), så to som kjører fix får samme id, og et nytt
navn i Git senere blir en omdøping. En tabell eller kolonne som hadde id i
<ref>, får den tilbake; kan ikke filene skille en kolonne som mistet id-en fra
en ny, gir den ingen id og sier hvorfor.
`--add-ids` uten `--changed-from` går bare i et repo uten én eneste commit: da kan
ingenting fra det være i Specly ennå, og alle tabeller og kolonner uten id får
den Specly ville gitt dem. Har repoet commits, trengs basen: Specly kjenner en
tabell eller kolonne uten id på navnet og bruker den id-en den alt har, og den
kan være en annen enn den fix ville skrevet.
Ellers endrer `fix` aldri innholdet: aldri en lenke, et unntak eller en
tekst noen har skrevet. Den rører ikke en fil med kommentarer (Specly
skriver ikke kommentarer, og `fix` sletter dem ikke), en fil der en nøkkel
står to ganger, eller en fil som ikke kan leses.
`fix` blir ferdig på én kjøring: når den har rettet noe i en fil (et YAML-anker,
tags i flytstil), sjekkes filen på nytt og det reglene gir, legges inn i samme
kjøring. En fil der noe fix skulle skrive, ikke kan skrives (filen har feil,
kommentarer, eller står slik sjekken ikke kan forutsi eksporten), får ingenting,
heller ikke formatet: aldri en halvveis rettet fil (det gjelder per fil; hver
fil skrives hel via en midlertidig fil `.<navn>.specly-fix-tmp~` ved siden av,
som slettes ved enhver feil, så et avbrudd etterlater den gamle eller den nye).
En symbolsk lenke står, og målet skrives; en skrivebeskyttet fil skrives ikke
(fix sier fra). En fil med to nøkler som blir samme tekst (1 og "1"), eller en
nøkkel som ikke er en enkel verdi, skrives aldri om for formatet. Hver fil skrives med sine egne linjeskift (CRLF inn, CRLF ut); en fil
uten linjeskift med det de fleste kontraktene har.

Exit-koder: 0 = ingen feil (advarsler stopper ikke); 1 = feil, eller et
funn `--fail-on` gjør til feil; 2 = sjekken kunne ikke kjøre (ukjent ref,
grunt utsjekk, git feilet, pyyaml mangler, ødelagt .specly.json eller
.specly/check.json, en kode som ikke finnes, en feil i skriptet, Python
eldre enn 3.9). `--fail-on <kode>` og `--ignore <kode>` og teamets egen
`.specly/check.json` ({"failOn": [...], "ignore": [...]}), som Specly aldri
skriver, styrer hva som stopper en PR. En kode treffer seg selv og kodene den
er et prefiks til ved et punktum (`lint.enum` treffer `lint.enum.flag`); en
kode som ikke treffer noe sjekken melder, stopper med exit 2. Står en kode i
både failOn og ignore, vinner failOn. En feil skjules bare av hele koden.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import uuid as uuidlib
import sys
import traceback
from pathlib import Path

if sys.version_info < (3, 9):
    print(f"Sjekken trenger Python 3.9 eller nyere, men kjører på {sys.version.split()[0]}. Kjør den slik: uv run --no-project --python 3.12 --with pyyaml python .specly/specly.py check.", file=sys.stderr)
    sys.exit(2)

try:
    import yaml
except ImportError:
    print("Sjekken trenger pyyaml. Kjør den slik: uv run --no-project --with pyyaml python .specly/specly.py check (eller pip install pyyaml).", file=sys.stderr)
    sys.exit(2)

MANIFEST_VERSION = 3
# Teamets egne innstillinger for sjekken, ved siden av skriptet. Specly skriver aldri denne filen.
CHECK_CONFIG = "check.json"
LINT_VERSION = 1
NO_DESCRIPTION = "lint.column.noDescription"
FORMAT_VERSION = 1
# Kodene som vises som én linje med antallet når det er flere enn SUMMARY_LIMIT av dem (uten --verbose).
SUMMARY_LIMIT = 10
SUMMARISED = {
    "rules.flag.wouldAdd": "kolonner som får flagg hvis flaggreglene kjøres i Specly (fix --apply-rules skriver dem der det er avgjort).",
    "rules.sort.wouldReorder": "tabeller som får ny kolonnerekkefølge hvis kolonnesorteringsreglene kjøres i Specly (fix --apply-rules flytter kolonnene der det er avgjort).",
    "rules.flag.undetermined": "kolonner og flaggregler der sjekken ikke kan si hvilke flagg flaggreglene gir.",
    "rules.sort.undetermined": "tabeller der sjekken ikke kan si hvilken rekkefølge kolonnesorteringsreglene gir.",
    "lineage.autoRename": "kolonner med nytt navn som kan omdøpe kolonnene de er kilde til.",
}
# Hver kode sjekken kan melde. `--fail-on` og `--ignore` må treffe en av dem, så en skrivefeil
# i en kode stopper bygget i stedet for å gjøre ingenting. En test i Specly sjekker at listen
# og kodene i skriptet er de samme.
CODES = (
    "concept.unreadable",
    "config.unreadable",
    "config.value",
    "diagram.unreadable",
    "export.refused",
    "file.encoding",
    "file.notRead",
    "file.unreadable",
    "format.differs",
    "json.parse",
    "lint.column.duplicateName",
    "lint.column.noDescription",
    "lint.column.noLineage",
    "lint.column.noName",
    "lint.concept.danglingColumn",
    "lint.concept.duplicateLink",
    "lint.concept.inheritedText",
    "lint.concept.missingException",
    "lint.concept.missingLink",
    "lint.concept.noUuid",
    "lint.concept.ownTextOverwritten",
    "lint.concept.ruleRegex",
    "lint.concept.staleRuleLink",
    "lint.concept.undetermined",
    "lint.customProperty.incomplete",
    "lint.dataProduct.danglingDiagram",
    "lint.dataProduct.danglingTable",
    "lint.diagram.danglingTable",
    "lint.enum.dataType",
    "lint.enum.flag",
    "lint.enum.sourceSystem",
    "lint.enum.status",
    "lint.enum.tableType",
    "lint.flag.duplicateName",
    "lint.lineage.dangling",
    "lint.lineage.duplicate",
    "lint.name.ambiguous",
    "lint.quality.dimension",
    "lint.quality.duplicateId",
    "lint.quality.duplicateName",
    "lint.quality.invalidName",
    "lint.quality.metric",
    "lint.quality.readAsText",
    "lint.quality.severity",
    "lint.relation.dangling",
    "lint.relation.skipped",
    "lint.table.duplicateName",
    "lint.table.noName",
    "lint.table.skipped",
    "lint.uuid.duplicate",
    "lint.uuid.fabricated",
    "lint.uuid.invalid",
    "lint.uuid.missing",
    "lint.value.place",
    "lint.value.text",
    "lint.value.type",
    "lineage.autoRename",
    "odcs.unreadable",
    "odps.unreadable",
    "rules.flag.undetermined",
    "rules.flag.wouldAdd",
    "rules.relation.undetermined",
    "rules.relation.wouldCreate",
    "rules.sort.undetermined",
    "rules.sort.wouldReorder",
    "schema.additionalProperties",
    "schema.anyOf",
    "schema.enum",
    "schema.required",
    "schema.type",
    "specly.version",
    "yaml.ambiguousPlain",
    "yaml.duplicateKey",
    "yaml.mergeKey",
    "yaml.parse",
)

UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
RULE_NAME = re.compile(r"^[A-Za-z0-9_]+$")
# Tekstfeltene en lenket kolonne arver fra begrepet, i den rekkefølgen Specly skriver unntakene.
CONCEPT_TEXTS = ("businessDescription", "developerNote", "downstreamName")
# Navnerommet Specly lager uuid i for et begrep uten (`entry_uuid`).
ENTRY_UUID_NS = uuidlib.UUID("5b0dc3f2-7a41-4e68-9d15-2c8ef0a63b71")
# Det sjekken antar om en kjøring av «Bruk reglene» (regelpanelets standardvalg).
DEFAULTS_NOTE = "Kjører noen «Bruk reglene» med standardvalgene («Behold egen tekst» på, «Sett datatype fra begrepet» av), så"
UUID_LIST_FILTERS = ("tableTypeFilter", "tableStatusFilter", "columnTypeFilter", "dataProductFilter")
DIMENSIONS = ["accuracy", "completeness", "conformity", "consistency", "coverage", "timeliness", "uniqueness"]
METRICS = ["nullValues", "missingValues", "invalidValues", "duplicateValues", "rowCount"]
CONFIG_SCHEMAS = {
    "datatypes.json": "datatype.schema.json",
    "flags.json": "flag.schema.json",
    "table_statuses.json": "status.schema.json",
    "column_statuses.json": "status.schema.json",
    "diagram_statuses.json": "status.schema.json",
    "data_product_statuses.json": "status.schema.json",
    "table_types.json": "tabletype.schema.json",
    "metadata_field_definitions.json": "metadata_field_definition.schema.json",
}

# Filene i config-mappen Specly leser: innstillinger (et objekt) og registre (en liste).
SETTING_FILES = ("odcs.json", "table_naming.json", "status_lists.json")
REGISTRY_FILES = (
    "datatypes.json",
    "flags.json",
    "table_statuses.json",
    "column_statuses.json",
    "diagram_statuses.json",
    "data_product_statuses.json",
    "source_systems.json",
    "person_roles.json",
    "persons.json",
    "metadata_field_definitions.json",
    "table_types.json",
    "relation_rules.json",
    "flag_rules.json",
    "column_sorting_rules.json",
)
# Stedene en innebygd verdi kan sendes til, ved siden av customProperties: et ukjent mål leser Specly ingenting fra.
SLOT_TARGETS = ("status", "businessName", "transformDescription", "transformLogic", "transformSourceObjects")
MATCH_MODES = ("startsWith", "endsWith", "contains", "regex")
# Det Specly bare leser som satt når verdien er `true`.
BOOLEANS = ("primaryKey", "required", "unique", "partitioned", "criticalDataElement", "deprecated")


def entity_types(item):
    """`entityTypes` i en feltdefinisjon: en liste, eller JSON-teksten til en."""
    value = item.get("entityTypes")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


# ---------- YAML med linjenummer ----------


class Map(dict):
    """En YAML-mapping som husker linjen til seg selv og til hver nøkkel, kolonnen den starter i, om den står i
    flytstil (`{a: 1}`), og nøklene uten noe etter kolonet (`description:`)."""

    line = 0
    column = 0
    flow = False

    def __init__(self):
        super().__init__()
        self.lines = {}
        self.empty = set()

    def line_of(self, key):
        return self.lines.get(key, self.line)


class Seq(list):
    """En YAML-liste som husker linjen til seg selv og til hvert element, og om den står i flytstil (`[a, b]`) over flere linjer."""

    line = 0
    flow = False
    multiline = False

    def __init__(self):
        super().__init__()
        self.lines = []

    def line_of(self, index):
        return self.lines[index] if index < len(self.lines) else self.line


class Loader(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    # Fylles av `load_yaml`: nøkler som står to ganger i samme mapping
    # (nøkkel, første linje, linje), og linjene til `<<`-nøkler.
    duplicates = None
    merges = None


def _construct_map(loader, node):
    out = Map()
    out.line = node.start_mark.line + 1
    out.column = node.start_mark.column
    out.flow = bool(node.flow_style)
    yield out
    merged = [k.start_mark.line + 1 for k, _ in node.value if k.tag == "tag:yaml.org,2002:merge"]
    if merged and loader.merges is not None:
        loader.merges.extend(merged)
    loader.flatten_mapping(node)
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, (str, int, float, bool, type(None))):
            key = str(key)
        line = key_node.start_mark.line + 1
        if key in out and not merged and loader.duplicates is not None:
            loader.duplicates.append((key, out.lines.get(key, line), line))
        out[key] = loader.construct_object(value_node, deep=True)
        out.lines[key] = line
        if getattr(value_node, "value", None) == "" and not getattr(value_node, "style", None) and value_node.tag.endswith(":null"):
            out.empty.add(key)


def _construct_seq(loader, node):
    out = Seq()
    out.line = node.start_mark.line + 1
    out.flow = bool(node.flow_style)
    out.multiline = node.end_mark.line > node.start_mark.line
    yield out
    for child in node.value:
        out.append(loader.construct_object(child, deep=True))
        out.lines.append(child.start_mark.line + 1)


Loader.add_constructor("tag:yaml.org,2002:map", _construct_map)
Loader.add_constructor("tag:yaml.org,2002:seq", _construct_seq)


def _construct_plain(loader, node):
    """En verdi uten anførselstegn slik Specly leser den: `yes`, `on`, `2024-01-01` og `12:30` er tekst der."""
    if node.style:
        return loader.construct_scalar(node)
    value = plain_scalar(node.value)
    if not isinstance(value, Plain):
        return value
    if value == "null":
        return None
    if value in ("true", "false"):
        return value == "true"
    return int(value) if INT.match(value) else float(value.replace(".inf", "inf").replace(".nan", "nan"))


for _tag in ("bool", "int", "float", "timestamp", "null"):
    Loader.add_constructor("tag:yaml.org,2002:" + _tag, _construct_plain)


def load_yaml(text):
    """YAML-teksten lest, med nøklene som står to ganger og linjene til `<<`-nøkler."""
    loader = Loader(text)
    loader.duplicates, loader.merges = [], []
    try:
        return loader.get_single_data(), loader.duplicates, loader.merges
    finally:
        loader.dispose()


def as_map(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def line_of(container, key, fallback=1):
    return container.line_of(key) if isinstance(container, (Map, Seq)) else fallback


# ---------- Funn ----------


class Stop(Exception):
    """Sjekken kan ikke kjøre (ukjent ref, grunt utsjekk, git feiler, `.specly.json` mangler): én linje, exit 2."""


class Findings:
    def __init__(self):
        self.items = []

    def add(self, level, file, line, rule, message, related=()):
        item = {"level": level, "file": file, "line": line, "rule": rule, "message": message, "related": [r for r in related if r]}
        self.items.append(item)
        return item

    def error(self, file, line, rule, message, related=()):
        return self.add("error", file, line, rule, message, related)

    def warning(self, file, line, rule, message, related=()):
        return self.add("warning", file, line, rule, message, related)


# ---------- Repoet ----------


class Column:
    def __init__(self, table, prop, index):
        self.table = table
        self.prop = prop
        self.name = str(prop.get("name") or "")
        self.id = prop.get("id") if isinstance(prop.get("id"), str) else None
        self.index = index
        self.line = line_of(table.properties, index, table.line)


class OldColumn:
    """En kolonne slik den sto i `--changed-from`: bare egenskapene."""

    def __init__(self, prop):
        self.prop = prop


class Table:
    # En tabell i en kontrakt Specly ikke kan lese: bare med for at navnet skal finnes.
    unreadable = False
    # Navnet fra en kontrakt som ikke kan leses som YAML: kolonnene er ukjente.
    ghost = False

    def __init__(self, file, contract, obj, line, settings):
        self.file = file
        self.contract = contract
        self.obj = obj
        self.line = line
        self.name = str(obj.get("name") or "")
        self.id = obj.get("id") if isinstance(obj.get("id"), str) else None
        custom = custom_properties(obj)
        server = as_map(next(iter(as_list(contract.get("servers"))), None))
        self.database = str(custom.get(settings.property("databaseName")) or server.get("catalog") or "")
        self.schema = str(custom.get(settings.property("schemaName")) or server.get("schema") or "")
        self.properties = as_list(obj.get("properties"))
        self.columns = [Column(self, p, i) for i, p in enumerate(self.properties) if isinstance(p, dict)]

    def column(self, name):
        exact = [c for c in self.columns if c.name == name]
        return (exact or [c for c in self.columns if c.name.lower() == name.lower()] or [None])[0]


def custom_properties(node):
    """`customProperties` som `{property: value}`."""
    out = {}
    for entry in as_list(as_map(node).get("customProperties")):
        if isinstance(entry, dict) and isinstance(entry.get("property"), str):
            out[entry["property"]] = entry.get("value")
    return out


# ---------- Formen Specly krever ----------
#
# En verdi av feil slag der Specly leser strukturen, gjør hele filen uleselig
# for Specly: den avvises, og ingenting fra den tas inn. En nøkkel som mangler,
# eller står med `null`, er i orden.

KINDS = {"list": "en liste", "text": "tekst", "map": "nøkler med verdier (en mapping)", "scalar": "én verdi (tekst eller tall)"}


def kind_of(value):
    if value is None:
        return "ingenting"
    if isinstance(value, bool):
        return "true/false"
    if isinstance(value, (int, float)):
        return "et tall"
    if isinstance(value, str):
        return "tekst"
    if isinstance(value, list):
        return "en liste"
    if isinstance(value, dict):
        return "nøkler med verdier (en mapping)"
    return "en verdi Specly ikke leser (" + type(value).__name__ + ")"


def is_kind(value, kind):
    if kind == "list":
        return isinstance(value, list)
    if kind == "text":
        return isinstance(value, str)
    if kind == "map":
        return isinstance(value, dict)
    return not isinstance(value, (list, dict))


class Shape:
    """Samler det første bruddet på formen, med linjen det står på."""

    def __init__(self):
        self.problem = None

    def fail(self, line, path, kind, value):
        if self.problem is None:
            self.problem = (line, f"{path} skal være {KINDS[kind]}, men er {kind_of(value)}. Specly kan ikke lese filen før det er rettet.")

    def key(self, node, key, path, kind):
        """Verdien under `key` når den har riktig slag; ellers meldes bruddet."""
        value = node.get(key)
        if value is None:
            return None
        if not is_kind(value, kind):
            self.fail(line_of(node, key), join_path(path, key), kind, value)
            return None
        return value

    def maps(self, node, key, path):
        """Oppføringene i listen under `key`, hver en mapping, med stien til hver."""
        items = self.key(node, key, path, "list")
        out = []
        for index, item in enumerate(items or []):
            if item is None:
                continue
            at = f"{join_path(path, key)}[{index}]"
            if isinstance(item, dict):
                out.append((at, item))
            else:
                self.fail(line_of(items, index), at, "map", item)
        return out

    def custom(self, node, path):
        for at, entry in self.maps(node, "customProperties", path):
            self.key(entry, "property", at, "text")

    def level(self, node, path, lists):
        self.key(node, "id", path, "scalar")
        self.key(node, "name", path, "text")
        self.custom(node, path)
        for key in lists:
            self.key(node, key, path, "list")
        for key in ("quality", "relationships"):
            self.maps(node, key, path)


def join_path(path, key):
    return f"{path}.{key}" if path else str(key)


def contract_problem(contract):
    """`(linje, melding)` for det første som gjør en kontrakt uleselig for Specly, ellers `None`."""
    kind = contract.get("kind")
    if kind != "DataContract":
        return line_of(contract, "kind"), f"kind skal være DataContract, men er {kind if isinstance(kind, str) else kind_of(kind)}. Specly kan ikke lese filen før det er rettet."
    version = contract.get("apiVersion")
    if not isinstance(version, str) or not version.startswith("v3."):
        return line_of(contract, "apiVersion"), f"apiVersion skal være en v3-versjon (for eksempel v3.2.0), men er {version if isinstance(version, str) and version else kind_of(version)}. Specly kan ikke lese filen før det er rettet."
    shape = Shape()
    shape.level(contract, "", ("tags", "servers", "slaProperties"))
    schema = shape.key(contract, "schema", "", "list")
    if schema is None and shape.problem is None:
        return line_of(contract, "schema"), "schema mangler eller er tom. Specly kan ikke lese filen: en kontrakt må ha schema som en liste med tabellen i."
    for index, obj in enumerate(schema or []):
        if obj is None:
            continue
        path = f"schema[{index}]"
        if not isinstance(obj, dict):
            shape.fail(line_of(schema, index), path, "map", obj)
            continue
        shape.level(obj, path, ("tags",))
        for at, prop in shape.maps(obj, "properties", path):
            shape.level(prop, at, ("tags", "transformSourceObjects", "properties"))
    return shape.problem


def odps_problem(doc):
    """Det første som gjør et dataprodukt uleselig for Specly."""
    kind = doc.get("kind")
    if kind != "DataProduct":
        return line_of(doc, "kind"), f"kind skal være DataProduct, men er {kind if isinstance(kind, str) else kind_of(kind)}. Specly kan ikke lese filen før det er rettet."
    version = doc.get("apiVersion")
    if not isinstance(version, str) or not version.startswith("v1."):
        return line_of(doc, "apiVersion"), f"apiVersion skal være en v1-versjon (for eksempel v1.1.0), men er {version if isinstance(version, str) and version else kind_of(version)}. Specly kan ikke lese filen før det er rettet."
    shape = Shape()
    shape.key(doc, "id", "", "scalar")
    shape.key(doc, "name", "", "text")
    shape.custom(doc, "")
    for key in ("tags", "support", "outputPorts", "inputPorts"):
        shape.key(doc, key, "", "list")
    entries = as_list(doc.get("customProperties"))
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("property") not in ("tables", "diagrams") or entry.get("value") is None:
            continue
        prop, value = entry["property"], entry["value"]
        at = f"customProperties[{index}].value ({prop})"
        if not isinstance(value, list):
            shape.fail(line_of(entry, "value", line_of(entries, index)), at, "list", value)
            continue
        for i, member in enumerate(value):
            named = isinstance(member, str) or (prop == "tables" and isinstance(member, dict) and isinstance(member.get("name"), str))
            if not named and shape.problem is None:
                wanted = "et tabellnavn, eller name og uuid" if prop == "tables" else "et diagramnavn"
                shape.problem = (line_of(value, i), f"{at}[{i}] skal være {wanted}, men er {kind_of(member)}. Specly kan ikke lese filen før det er rettet.")
    return shape.problem


def diagram_problem(data):
    """Det første som gjør en diagramfil uleselig for Specly. `None` også for en fil som ikke er et diagram."""
    if data is None:
        return None
    if not isinstance(data, dict):
        return f"Filen skal være et JSON-objekt, men er {kind_of(data)}. Specly kan ikke lese filen før det er rettet."
    shape = Shape()

    def check():
        shape.key(data, "uuid", "", "text")
        shape.key(data, "name", "", "text")
        shape.maps(data, "tables", "")
        shape.maps(data, "relations", "")
        shape.key(data, "relationBreakpoints", "", "map")
        shape.key(data, "sourceSystems", "", "list")
        return shape.problem[1] if shape.problem else None

    uuid = data.get("uuid")
    if not isinstance(uuid, str) or not uuid:
        if "uuid" in data and check():
            return shape.problem[1]
        if "name" in data and ("tables" in data or "relations" in data):
            return "Diagrammet har name og tables, men ingen uuid. Specly kan ikke lese filen: et nytt diagram trenger en uuid du lager selv (uuid v4, for eksempel fra uuidgen)."
        return None
    problem = check()
    if problem:
        return problem
    for index, item in enumerate(as_list(data.get("tables"))):
        if not isinstance(item, dict):
            return f"tables[{index}] skal være nøkler med verdier, men er {kind_of(item)}. Specly kan ikke lese filen før det er rettet."
    return None


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and value not in (float("inf"), float("-inf"))


class Settings:
    """Det sjekken trenger av `.specly.json` og `odcs.json`."""

    def __init__(self, manifest, odcs):
        self.manifest = manifest
        self.odcs = odcs
        self.mappings = as_map(odcs.get("builtinFieldMappings"))
        self.shorthand = odcs.get("referenceStyle") == "shorthand"
        self.quote_all = odcs.get("quoteAllStrings") in (True, "true")

    def property(self, builtin):
        """Navnet på custom property-en en innebygd verdi skrives i."""
        return as_map(self.mappings.get(builtin)).get("odcsPropertyName") or builtin

    def target(self, builtin):
        return as_map(self.mappings.get(builtin)).get("odcsTarget")

    def value(self, node, builtin):
        """Verdien en innebygd verdi har på `node`, der innstillingene sender den."""
        target = self.target(builtin)
        if target and target not in ("customProperties", "tags"):
            return node.get(target)
        return custom_properties(node).get(self.property(builtin))

    def downstream_name(self, prop):
        """Nedstrømsnavnet Specly leser (odcs_import.rs): med `columnBusinessNameSource: downstreamName` en
        `businessName` som ikke er tom og ikke lik kolonnens navn, ellers den innebygde verdien der den står."""
        name = prop.get("businessName")
        if self.odcs.get("columnBusinessNameSource") == "downstreamName" and isinstance(name, str) and name:
            return "" if name == prop.get("name") else name
        return self.value(prop, "downstreamName")


class Repo:
    def __init__(self, root, findings, overrides=None):
        self.findings = findings
        self.root = root
        # Tekstene fix har skrevet i en tidligere runde (sti -> tekst med LF), lagt over filene på disk.
        self.overrides = overrides or {}
        manifest_path = root / ".specly.json"
        if not manifest_path.is_file():
            raise Stop(f"Fant ikke {manifest_path}. Skriptet må ligge i .specly-mappen Specly skrev det til.")
        try:
            manifest = json.loads(manifest_path.read_bytes().decode("utf-8-sig"))
        except ValueError as e:
            raise Stop(f"{manifest_path} er ikke gyldig JSON ({e}). Specly skriver filen: hent den tilbake fra Git (git checkout -- {manifest_path.name}), og ikke endre den for hånd.")
        if not isinstance(manifest, dict):
            raise Stop(f"{manifest_path} skal være et JSON-objekt. Specly skriver filen: hent den tilbake fra Git, og ikke endre den for hånd.")
        self.texts = {}
        self.rels = {}
        self.crlf = set()
        self.lf = set()
        self.jsons = {}
        self.broken_yaml = set()
        root_folder = [p for p in str(manifest.get("rootFolder") or "").split("/") if p]
        self.top = root
        for part in reversed(root_folder):
            if self.top.name != part:
                raise Stop(f"{manifest_path} sier rootFolder {manifest.get('rootFolder')!r}, men skriptet ligger i {root}.")
            self.top = self.top.parent
        self.config_dir = root / str(manifest.get("configFolder") or "Config")
        self.settings = Settings(manifest, as_map(self.read_json(self.config_dir / "odcs.json", {})))
        self.broken_settings = []
        for name in SETTING_FILES:
            path = self.config_dir / name
            if path.is_file():
                ok, value = self.json_of(path)
                if not ok or not isinstance(value, dict):
                    self.broken_settings.append(self.rel(path))
        self.tables = []
        self.by_name = {}
        self.columns_by_id = {}
        self.concepts = []
        self.concept_problems = []
        self.contract_paths = []
        self.concept_paths = []
        self.data_products = []
        self.diagrams = []
        self.unparsed_diagram_names = []
        self.datatypes_path = self.config_dir / "datatypes.json"
        self.tables_dir = self.folder("tablesFolder", "tablesAtRepoRoot", "Tables")
        self.data_products_dir = self.folder("dataProductsFolder", "dataProductsAtRepoRoot", "DataProducts")
        self.diagrams_dir = self.root / str(manifest.get("diagramsFolder") or "Diagrams")
        self.concepts_dir = self.folder("conceptsFolder", "conceptsAtRepoRoot", "Concepts")
        # Kildesystemene står der eksportoppsettet sier (`source_systems_path` i config.rs), som JSON eller YAML.
        folder = str(manifest.get("sourceSystemsFolder") or "").strip("/")
        base = (self.top if manifest.get("sourceSystemsAtRepoRoot") else root) / folder if folder else self.config_dir
        self.source_systems_path = base / f"source_systems.{'yaml' if manifest.get('sourceSystemsFormat') == 'yaml' else 'json'}"

    def registry_path(self, name):
        """Stien til registerfilen `name`: kildesystemene der oppsettet sier, de andre i config-mappen."""
        return self.source_systems_path if name == "source_systems.json" else self.config_dir / name

    def rel(self, path):
        # Kalles for hvert funn og hver fil: en oppslagstabell i stedet for pathlib hver gang.
        rel = self.rels.get(path)
        if rel is None:
            rel = self.rels[path] = path.relative_to(self.top).as_posix()
        return rel

    def folder(self, key, at_root_key, default):
        base = self.top if self.settings.manifest.get(at_root_key) else self.root
        return base / str(self.settings.manifest.get(key) or default)

    def read_text(self, path):
        """Teksten i en fil, eller `None` (meldt én gang) når den ikke er UTF-8."""
        if path not in self.texts:
            try:
                raw = path.read_bytes().decode("utf-8")
                # Linjeskiftet er ikke innhold: CRLF (en utsjekk med autocrlf) leses som LF, og fix skriver filen
                # tilbake med sine egne linjeskift (`eol`). Et enkelt CR rører vi ikke: Specly melder det som et problem.
                if "\r\n" in raw:
                    self.crlf.add(path)
                elif "\n" in raw:
                    self.lf.add(path)
                raw = self.overrides.get(path, raw.replace("\r\n", "\n"))
                self.texts[path] = raw
            except UnicodeDecodeError as e:
                self.texts[path] = None
                line = path.read_bytes()[: e.start].count(b"\n") + 1
                self.findings.error(self.rel(path), line, "file.encoding", "Filen er ikke UTF-8. Specly leser tegnene den ikke forstår som � og tar dem inn slik. Lagre filen som UTF-8.")
            except OSError as e:
                self.texts[path] = None
                self.findings.error(self.rel(path), 1, "file.unreadable", f"Filen kan ikke leses: {e}.")
        return self.texts[path]

    def eol(self, path, fallback):
        """Linjeskiftet fix skriver filen med: filens eget, ellers `fallback`."""
        self.read_text(path)
        if path in self.crlf:
            return "\r\n"
        if path in self.lf:
            return "\n"
        return fallback

    def common_eol(self):
        """Linjeskiftet de fleste kontraktene har (sjekken har lest dem alle): det en fil uten linjeskift skrives med."""
        crlf = sum(1 for p in self.contract_paths if p in self.crlf)
        lf = sum(1 for p in self.contract_paths if p in self.lf)
        return "\r\n" if crlf > lf else "\n"

    def json_of(self, path):
        """`(lest, verdi)` for en JSON-fil. En fil som ikke kan leses, meldes én gang."""
        if path not in self.jsons:
            text = self.read_text(path) if path.is_file() else None
            if text is None:
                self.jsons[path] = (False, None)
            else:
                try:
                    # Et BOM først i filen meldes av formatsjekken.
                    self.jsons[path] = (True, json.loads(text[1:] if text.startswith("\ufeff") else text))
                except ValueError as e:
                    self.jsons[path] = (False, None)
                    if not text.strip():
                        self.findings.error(self.rel(path), 1, "json.parse", "Filen er tom. Specly lister den som uleselig og leser ikke noe fra den før den har innhold. Legg innholdet tilbake, eller slett filen.")
                        return self.jsons[path]
                    self.findings.error(self.rel(path), getattr(e, "lineno", 1), "json.parse", f"Filen er ikke gyldig JSON: {e}. Specly leser da ingenting fra den. Rett filen.")
        return self.jsons[path]

    def read_json(self, path, fallback):
        ok, value = self.json_of(path)
        return value if ok else fallback

    def registry_data(self, path):
        """`(lest, verdi)` for en registerfil: JSON, eller YAML for kildesystemene i `source_systems.yaml`."""
        if path.suffix != ".yaml":
            return self.json_of(path)
        if path not in self.jsons:
            text = self.read_text(path) if path.is_file() else None
            data = self.read_yaml(path, text) if text is not None else None
            self.jsons[path] = (text is not None and path not in self.broken_yaml, data)
        return self.jsons[path]

    def read_yaml(self, path, text, first_line=0):
        """YAML-teksten lest. `None` også for en fil som ikke kan leses (meldt)."""
        file = self.rel(path)
        try:
            data, duplicates, merges = load_yaml(text)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            problem = getattr(e, "problem", None) or str(e)
            self.broken_yaml.add(path)
            self.findings.error(file, (mark.line + 1 if mark else 1) + first_line, "yaml.parse", f"Filen er ikke gyldig YAML: {problem}. Rett filen.")
            return None
        for key, first, line in duplicates:
            self.broken_yaml.add(path)
            self.findings.error(file, line + first_line, "yaml.duplicateKey", f"Nøkkelen {key} står to ganger i samme blokk (første gang på linje {first + first_line}). Specly leser bare den siste, uten å si fra. Fjern den ene.")
        for line in merges:
            self.broken_yaml.add(path)
            self.findings.error(file, line + first_line, "yaml.mergeKey", "Specly leser ikke `<<` (YAML merge): det som hentes inn med den, blir ikke lest. Skriv nøklene rett ut.")
        return data

    def load(self):
        for path in sorted(self.tables_dir.rglob("*.odcs.yaml")) if self.tables_dir.is_dir() else []:
            self.contract_paths.append(path)
            text = self.read_text(path)
            if text is not None:
                self.load_contract(path, text, self.tables)
        for table in self.tables:
            self.by_name.setdefault(table.name.lower(), []).append(table)
            for column in table.columns:
                if column.id:
                    self.columns_by_id.setdefault(column.id.lower(), []).append(column)
        concepts = self.concepts_dir
        for path in sorted(concepts.glob("*.md")) if concepts.is_dir() else []:
            self.concept_paths.append(path)
            text = self.read_text(path)
            if text is None:
                continue
            file = self.rel(path)
            # Et BOM først i filen leser Specly bort; formatsjekken melder det.
            text = text[1:] if text.startswith("\ufeff") else text
            if not text.strip():
                self.concept_problems.append((file, 1, "Filen er tom. Specly lister den som uleselig og leser ikke inn begrepet før filen har innhold. Legg innholdet tilbake, eller slett filen hvis begrepet skal bort."))
                continue
            # Specly kjenner bare igjen toppen når første linje er `---` og en senere linje lukker den.
            first = text.split("\n", 1)[0].rstrip()
            front, first_line, body = frontmatter(text)
            if first == "---" and not first_line:
                self.concept_problems.append((file, 1, "Toppen (mellom to linjer med `---`) er ikke lukket. Specly leser da hele filen som beskrivelse, og begrepet blir et nytt begrep uten lenker og regler. Legg til en linje med `---` etter toppen."))
                continue
            data = self.read_yaml(path, front, first_line) if front.strip() else None
            if front.strip() and data is not None and not isinstance(data, dict):
                self.concept_problems.append((file, first_line + 1, "Toppen av begrepsfilen skal være nøkler med verdier (en YAML-mapping). Specly kan ikke lese filen. Rett toppen."))
            if isinstance(data, dict):
                self.concepts.append(Concept(file, data, first_line, body, path))
        for path in sorted(self.data_products_dir.rglob("*.odps.yaml")) if self.data_products_dir.is_dir() else []:
            text = self.read_text(path)
            if text is not None:
                self.data_products.append((path, self.read_yaml(path, text)))
        for path in sorted(self.diagrams_dir.rglob("*.json")) if self.diagrams_dir.is_dir() else []:
            ok, data = self.json_of(path)
            if ok:
                self.diagrams.append((path, data))
            else:
                name = re.search(r'"name"\s*:\s*"((?:[^"\\]|\\.)*)"', self.texts.get(path) or "")
                if name:
                    self.unparsed_diagram_names.append(json.loads(f'"{name.group(1)}"'))

    def format_files(self):
        """Filene formatet sjekkes i, med hva slags fil hver er."""
        for path in self.contract_paths:
            yield path, "contract"
        for path in self.concept_paths:
            yield path, "concept"
        data_products = self.data_products_dir
        for path in sorted(data_products.rglob("*.yaml")) if data_products.is_dir() else []:
            if not path.name.endswith(".odcs.yaml") and path != self.source_systems_path:
                yield path, "odps" if path.name.endswith(".odps.yaml") else "yaml"
        if self.source_systems_path.suffix == ".yaml":
            yield self.source_systems_path, "registry"
        for path in [self.root / ".specly.json"] + (sorted(self.config_dir.glob("*.json")) if self.config_dir.is_dir() else []):
            yield path, "json"
        for path in sorted(self.diagrams_dir.rglob("*.json")) if self.diagrams_dir.is_dir() else []:
            yield path, "json"

    def registry(self, name):
        """Oppføringene i en config-fil, eller `None` når filen ikke finnes eller ikke kan leses."""
        ok, value = self.registry_data(self.registry_path(name))
        return [e for e in value if isinstance(e, dict)] if ok and isinstance(value, list) else None

    def load_contract(self, path, text, into):
        """Tabellene i en kontrakt. En kontrakt Specly ikke kan lese, meldes, og tabellene
        den nevner, tas likevel med (merket `unreadable`) så referanser til dem ikke meldes i tillegg."""
        file = self.rel(path)
        contract = self.read_yaml(path, text)
        problem = None
        if path in self.broken_yaml and contract is None:
            self.ghost_tables(file, text, into)
            return
        if contract is None:
            problem = (1, "Filen er tom (eller har bare kommentarer). Specly lister den som uleselig og leser ikke inn tabellen før filen har innhold. Legg innholdet tilbake, eller slett filen hvis tabellen skal bort.")
        elif not isinstance(contract, dict):
            problem = (1, "Kontrakten skal være nøkler med verdier (en YAML-mapping). Specly kan ikke lese filen. Rett filen.")
        else:
            problem = contract_problem(contract)
        if problem:
            self.findings.error(file, problem[0], "odcs.unreadable", problem[1])
        schema = as_list(as_map(contract).get("schema"))
        for index, obj in enumerate(schema):
            if isinstance(obj, dict):
                try:
                    table = Table(file, contract, obj, line_of(schema, index), self.settings)
                    table.index = index
                except (TypeError, AttributeError):
                    continue
                table.unreadable = bool(problem)
                kind = obj.get("physicalType")
                if not problem and isinstance(kind, str) and kind not in ("table", "view") and not self.physical_type_read():
                    self.findings.error(file, line_of(obj, "physicalType", table.line), "lint.table.skipped", f"Tabellen {table.name} har physicalType {kind}. Uten et felt som er satt til å lese physicalType hopper Specly over alt som ikke er table eller view: tabellen leses som slettet, og relasjonene, dataproduktene og diagrammene som nevner den mister den. Skriv table eller view.")
                    continue
                into.append(table)

    def physical_type_read(self):
        """Om et felt eller en innebygd verdi er satt til å lese `physicalType` på tabellobjektet."""
        fields = self.registry("metadata_field_definitions.json") or []
        return any(e.get("odcsTarget") == "physicalType" for e in fields) or any(as_map(m).get("odcsTarget") == "physicalType" for m in self.settings.mappings.values())

    def ghost_tables(self, file, text, into):
        """Tabellnavnene i en kontrakt som ikke kan leses som YAML, så ingenting som peker på dem meldes som borte."""
        lines = text.split("\n")
        start = next((i for i, l in enumerate(lines) if l.rstrip() == "schema:"), None)
        found, current = [], None
        for line in lines[(start + 1 if start is not None else len(lines)):]:
            if line and not line[0].isspace() and not line.startswith("-"):
                break
            dash = re.match(r"^(\s*)- ", line)
            if dash and (current is None or len(dash.group(1)) <= current[0]):
                current = [len(dash.group(1)), {}]
                found.append(current[1])
            match = re.match(r"^\s*(?:- )?(id|name):\s*[\"']?([^\"'#\n]*?)[\"']?\s*$", line)
            if match and current and (dash or len(line) - len(line.lstrip()) == current[0] + 2):
                current[1].setdefault(match.group(1), match.group(2))
        for entry in found:
            if entry.get("name"):
                table = Table(file, {}, {"name": entry["name"], "id": entry.get("id")}, 1, self.settings)
                table.unreadable = table.ghost = True
                into.append(table)

    def resolve(self, reference):
        """`[<database>.<schema>.]<table>.<column>` -> (tabell, kolonne, hva som mangler)."""
        parts = split_reference(reference)
        if len(parts) < 2:
            return None, None, "format"
        qualifier, table_name, column_name = parts[:-2], parts[-2], parts[-1]
        candidates = self.by_name.get(table_name.lower(), [])
        exact = [t for t in candidates if t.name == table_name]
        candidates = exact or candidates
        if len(qualifier) == 2:
            candidates = [t for t in candidates if (t.database.lower(), t.schema.lower()) == (qualifier[0].lower(), qualifier[1].lower())]
        if not candidates:
            return None, None, "table"
        if len(candidates) > 1:
            return candidates[0], None, "ambiguous"
        if candidates[0].ghost:
            return candidates[0], None, None
        column = candidates[0].column(column_name)
        return candidates[0], column, None if column else "column"


def split_reference(reference):
    """Deler på `.`; `\\.` er et punktum i et navn."""
    parts, current, i = [], "", 0
    while i < len(reference):
        if reference[i] == "\\" and reference[i + 1 : i + 2] == ".":
            current += "."
            i += 2
        elif reference[i] == ".":
            parts.append(current)
            current = ""
            i += 1
        else:
            current += reference[i]
            i += 1
    return parts + [current]


def frontmatter(text):
    """Teksten mellom de to første `---`-linjene, linjen den starter etter, og teksten under."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return "", 0, text
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip() == "---":
            return "\n".join(lines[1:index]), 1, "\n".join(lines[index + 1 :])
    return "", 0, text


class Concept:
    def __init__(self, file, data, first_line, body, path=None):
        self.file = file
        self.data = data
        self.first_line = first_line
        self.name = str(data.get("name") or Path(file).stem)
        self.path = path
        self.body = body
        given = data.get("uuid")
        self.has_uuid = isinstance(given, str) and bool(given)
        # Uten uuid i filen gir Specly begrepet en uuid laget av navnet.
        self.uuid = given if self.has_uuid else str(uuidlib.uuid5(ENTRY_UUID_NS, f"businessConcepts:{self.name}"))
        # Teksten slik Specly holder den: beskrivelsen trimmet, de andre som de står.
        self.text = {
            "businessDescription": body.strip(),
            "developerNote": data.get("developerNote") if isinstance(data.get("developerNote"), str) else "",
            "downstreamName": data.get("downstreamName") if isinstance(data.get("downstreamName"), str) else "",
        }
        self.data_type = data.get("dataType") if isinstance(data.get("dataType"), str) else ""


# ---------- Sammenligning med en annen branch ----------


class Delta:
    """Forskjellen på en config-fil i `--changed-from` og nå. `changed`: JSON-en er en annen (ikke bare formatet).
    For et register (en liste med oppføringer, kjent på uuid, ellers navn): `names` (trimmet, små bokstaver) og
    `uuids` (små bokstaver) og `keys` (systemKey) for hver oppføring som er lagt til, tatt bort eller endret, gammelt
    og nytt navn. JSON sammenlignes som tekst med sorterte nøkler, så `true` og `1` er ulike, som for Specly.
    `everything`: filen kan ikke leses på den ene siden, så hver verdi regnes som endret. `old`/`new`: oppføringene."""

    def __init__(self, old, new):
        same = lambda a, b: json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
        self.changed = not same(old, new)
        self.everything = self.changed and (old is None or new is None)
        self.names, self.uuids, self.keys = set(), set(), set()
        self.old = [e for e in old if isinstance(e, dict)] if isinstance(old, list) else []
        self.new = [e for e in new if isinstance(e, dict)] if isinstance(new, list) else []
        if not self.changed or self.everything:
            return
        key = lambda e: str(e.get("uuid")).lower() if e.get("uuid") else f"name:{e.get('name')}"
        old_entries = {key(e): e for e in old if isinstance(e, dict)} if isinstance(old, list) else {}
        new_entries = {key(e): e for e in new if isinstance(e, dict)} if isinstance(new, list) else {}
        for k in set(old_entries) | set(new_entries):
            a, b = old_entries.get(k), new_entries.get(k)
            if same(a, b):
                continue
            for entry in (a, b):
                if entry is None:
                    continue
                if isinstance(entry.get("name"), str):
                    self.names.add(loose(entry["name"]))
                if isinstance(entry.get("uuid"), str):
                    self.uuids.add(entry["uuid"].lower())
                if isinstance(entry.get("systemKey"), str):
                    self.keys.add(entry["systemKey"])

    def names_any(self, names=(), uuids=(), keys=()):
        """Om en av verdiene (navn, uuid eller systemKey) er blant dem endringen rører."""
        return self.everything or any(loose(n) in self.names for n in names if isinstance(n, str)) or any(u.lower() in self.uuids for u in uuids if isinstance(u, str)) or any(k in self.keys for k in keys if isinstance(k, str))


class Baseline:
    """Det som er endret siden `ref`, og hva de endrede kontraktene sa der."""

    def __init__(self, repo, ref):
        self.repo = repo
        self.changed = set()
        self.column_renames = {}
        self.table_renames = {}
        self.old_columns = {}
        self.old_table_files = {}
        self.old_diagram_files = {}
        # Kolonnene i kontraktene endringene rører, slik de sto: tabell (id og navn) -> kolonne (id og navn) -> egenskaper.
        self.old_props = {}
        self.old_tables = {}
        base = self.merge_base(ref)
        self.base = base
        self.deltas = {}
        old_paths = set()
        # -z: git skriver da stiene som de er (uten -z står et navn med æøå i anførselstegn med \303\270).
        # Hver post er status og én sti, eller for en flytting/kopi (R, C) status, gammel og ny sti.
        fields = self.git("diff", "--name-status", "--relative", "-z", base).split("\0")[:-1]
        at = 0
        while at < len(fields):
            status = fields[at]
            count = 2 if status[:1] in ("R", "C") else 1
            paths = fields[at + 1 : at + 1 + count]
            at += 1 + count
            self.changed.update(paths)
            if not status.startswith("A"):
                old_paths.add(paths[0])
        self.changed.update(self.git("ls-files", "--others", "--exclude-standard", "-z").split("\0")[:-1])
        current_tables = {t.id.lower(): t for t in repo.tables if t.id}
        for path in sorted(p for p in old_paths if p.endswith(".odcs.yaml")):
            old_tables = []
            try:
                contract = yaml.load(self.git("show", f"{base}:./{path}"), Loader=Loader)
            except yaml.YAMLError:
                continue
            for obj in as_list(as_map(contract).get("schema")):
                if isinstance(obj, dict):
                    old_tables.append(Table(path, contract, obj, 1, repo.settings))
            for old in old_tables:
                now = current_tables.get(old.id.lower()) if old.id else None
                self.old_table_files[old.name.lower()] = path
                if old.id:
                    self.old_table_files[old.id.lower()] = path
                if now is not None and now.name != old.name:
                    self.table_renames[old.name.lower()] = now.name
                self.old_columns[(old.id or old.name).lower()] = {c.name: c.id for c in old.columns}
                self.old_tables.update({k.lower(): old for k in (old.id, old.name) if k})
                props = {}
                for column in old.columns:
                    props.update({k.lower(): column.prop for k in (column.id, column.name) if k})
                self.old_props.update({k.lower(): props for k in (old.id, old.name) if k})
                for column in old.columns:
                    current = repo.columns_by_id.get(column.id.lower(), []) if column.id else []
                    if current and current[0].name != column.name:
                        self.column_renames[(old.name.lower(), column.name.lower())] = current[0].name
        diagrams_prefix = repo.rel(repo.diagrams_dir) + "/"
        for path in sorted(p for p in old_paths if p.endswith(".json") and p.startswith(diagrams_prefix)):
            try:
                data = json.loads(self.git("show", f"{base}:./{path}"))
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("name"), str):
                self.old_diagram_files[data["name"].lower()] = path

    def column_history(self, column):
        """`"new"` når endringene lager kolonnen, egenskapene den hadde når den fantes, `None` når filen ikke er endret."""
        if column.table.file not in self.changed:
            return None
        for table_key in (column.table.id, column.table.name):
            if table_key and table_key.lower() in self.old_props:
                old = self.old_props[table_key.lower()]
                return next((old[k.lower()] for k in (column.id, column.name) if k and k.lower() in old), "new")
        return "new"

    def config_delta(self, name):
        """Hva endringene gjør med config-filen `name`: `None` når filen ikke er endret, ellers en `Delta`."""
        if name not in self.deltas:
            path = self.repo.registry_path(name)
            rel = self.repo.rel(path)
            delta = None
            if rel in self.changed:
                shown = subprocess.run(["git", "show", f"{self.base}:./{rel}"], cwd=self.repo.top, capture_output=True)
                try:
                    text = shown.stdout.decode("utf-8-sig")
                    old = (load_yaml(text)[0] if path.suffix == ".yaml" else json.loads(text)) if shown.returncode == 0 else []
                except (ValueError, yaml.YAMLError):
                    old = None
                ok, new = self.repo.registry_data(path) if path.is_file() else (True, [])
                delta = Delta(old, new if ok else None)
            self.deltas[name] = delta
        return self.deltas[name]

    def merge_base(self, ref):
        """Der branchen deler seg fra `ref`. Stopper med en forklaring når det ikke går."""
        known = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=self.repo.top, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if known.returncode != 0:
            raise Stop(f"Fant ikke {ref} i dette repoet. Hent den først (git fetch origin {ref.removeprefix('origin/')}), eller gi --changed-from en ref som finnes.")
        result = subprocess.run(["git", "merge-base", ref, "HEAD"], cwd=self.repo.top, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0 or not result.stdout.strip():
            shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=self.repo.top, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip() == "true"
            if shallow:
                raise Stop(f"Historikken er for kort til å finne der branchen deler seg fra {ref} (repoet er et grunt utsjekk). Hent hele historikken: i CI sett fetch-depth: 0 på checkout, ellers kjør git fetch --unshallow.")
            raise Stop(f"Fant ingen felles forfader mellom {ref} og HEAD. Sjekk at {ref} er branchen denne PR-en skal inn i.")
        return result.stdout.strip()

    def files_of(self, files, *keys):
        """Filene som hadde `keys` (navn eller id) i `ref`, så et funn om noe som er borte eller har skiftet navn vises selv om filen med funnet ikke er endret."""
        return [files[k.lower()] for k in keys if isinstance(k, str) and k.lower() in files]

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo.top, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise Stop(f"git {' '.join(args)} feilet: {result.stderr.strip()}")
        return result.stdout


# ---------- Sjekkene ----------


class Check:
    def __init__(self, repo, baseline, lineage_required, check_format=True, strict=False):
        self.repo = repo
        self.f = repo.findings
        self.baseline = baseline
        self.lineage_required = lineage_required
        self.check_format = check_format
        self.strict = strict
        # Registerfil -> verdiene kontraktene bruker som mangler der -> funnene (`fix --add-values`).
        self.missing_values = {}
        self.rule_ids = {}
        # Regel- og relasjons-id -> [(fil, linje, hva)], første gang i hver fil: samme id i to kontrakter (`ids`).
        self.rules_by_id = {}
        self.relations_by_id = {}
        self.skipped = []
        self.format_skipped = ""
        self.reformatted = {}
        # Fil -> (anførselstegnet, [(linje, fra, til, verdi, funnet)]) for verdiene en YAML 1.1-leser leser som noe annet.
        self.ambiguous = {}
        # Det fix skriver for begrepslenkene: nye lenker per begrepsfil, arvet tekst per kontrakt.
        self.concept_writes = {}
        self.concept_uuids = {}
        self.column_texts = {}
        self.bad_concepts = set()
        # Det fix skriver etter reglene: flagg per kontrakt, ny kolonnerekkefølge per kontrakt.
        self.flag_writes = {}
        self.flag_entries = None
        self.baseline_ref = None
        self.column_orders = {}
        # Kolonne (id) -> flaggene (uuid) flaggreglene ville lagt til.
        self.rule_flags = {}
        # Config-fil -> om endringen i den kan gi et annet utfall av reglene (`config_changed`), og hva reglene nevner.
        self.counted = {}
        self.mentions = {}
        # Registerfiler Specly ikke kan lese: verdiene i dem er da ukjente, ikke borte.
        self.broken_registries = set()
        self.config_files()
        # Et nivå kan bruke et annet nivås statusliste (status_lists.json).
        uses = as_map(repo.read_json(repo.config_dir / "status_lists.json", {}))
        files = {"table": "table_statuses.json", "column": "column_statuses.json", "diagram": "diagram_statuses.json", "dataProduct": "data_product_statuses.json"}
        # Nivå -> filen med statuslisten nivået bruker; nivåets egen fil -> den samme.
        self.status_used = {level: files.get(uses.get(level), files[level]) if isinstance(uses.get(level), str) else files[level] for level in files}
        self.status_files = {files[level]: self.status_used[level] for level in ("table", "column")}
        self.statuses = {own: status_names(self.registry(used)) for own, used in self.status_files.items()}
        flags = self.registry("flags.json")
        self.flags = None if flags is None else Names([str(e.get("name")) for e in flags] + [repo.settings.property("businessKey")])
        self.table_types = self.names("table_types.json")
        self.source_systems = self.names("source_systems.json")
        lint = as_map(repo.read_json(repo.root / ".specly/lint.json", {})).get("rules")
        self.lint_rules = lint if isinstance(lint, dict) else {}
        # Filene Specly har skrevet til branchen (stier fra toppen av repoet).
        self.exported = {f for f in as_list(as_map(repo.read_json(repo.root / ".specly/files.json", {})).get("files")) if isinstance(f, str)}

    def registry(self, name):
        """Oppføringene i et register, eller `None` når Git ikke har en fil Specly kan lese for det."""
        return None if name in self.broken_registries else self.repo.registry(name)

    def same_uuid(self, holders, what, advice):
        """Samme uuid i to filer: Specly leser ingen av dem, så begge meldes."""
        for group in holders.values():
            for file, line in group if len({f for f, _ in group}) > 1 else []:
                other = next(f for f, _ in group if f != file)
                self.f.error(file, line, "lint.uuid.duplicate", f"{what} har samme uuid som {other}. Specly leser da ingen av filene. {advice}", [other])

    def names(self, registry):
        """Navnene i et register med små bokstaver, eller `None` når Git ikke har (en lesbar) fil for det."""
        entries = self.registry(registry)
        return None if entries is None else Names(e["name"] for e in entries if isinstance(e.get("name"), str))

    def run(self):
        self.versions()
        broken = self.repo.broken_settings
        if broken:
            self.skipped.append(f"{', '.join(broken)} kan ikke leses. Specly holder alt tilbake til den er rettet, så sjekken hopper over formatsjekken og alt som avhenger av innstillingene (verdier, statuser, kilder, begreper).")
        datatypes = self.datatypes()
        self.table_names()
        for table in self.repo.tables:
            if not table.unreadable and not broken:
                self.table(table, datatypes)
        self.ids()
        self.concepts()
        if not broken:
            self.concept_links()
            self.flag_rules()
            self.sorting_rules()
            self.relation_rules()
            self.auto_renames()
        self.diagrams()
        self.data_products()
        self.ambiguous_plain()
        self.export_refusals()
        self.files_not_read()
        self.settings_values()
        if self.check_format and not broken and not self.format_skipped:
            self.format()
        elif self.check_format and self.format_skipped:
            self.skipped.append(self.format_skipped)

    def settings_values(self):
        """`quoteAllStrings` leser Specly som true bare for true og teksten true: alt annet er false."""
        value = self.repo.settings.odcs.get("quoteAllStrings")
        if value is not None and not isinstance(value, bool) and value not in ("true", "false"):
            file = self.repo.rel(self.repo.config_dir / "odcs.json")
            self.f.warning(file, 1, "config.value", f"quoteAllStrings er {value!r}, ikke true eller false. Specly leser det som false. Rett verdien.")
            self.format_skipped = "quoteAllStrings i odcs.json har feil slag verdi, så formatsjekken er hoppet over: den ville meldt hver fil."

    def versions(self):
        root = self.repo.root
        for path, key, expected in ((root / ".specly.json", "version", MANIFEST_VERSION), (root / ".specly/lint.json", "version", LINT_VERSION), (root / ".specly/format.json", "version", FORMAT_VERSION)):
            found = as_map(self.repo.read_json(path, {})).get(key)
            if found is not None and found != expected:
                self.f.warning(self.repo.rel(path), 1, "specly.version", f"Filen har versjon {found}, sjekken kjenner versjon {expected}. Hent ny sjekk: gjør en skriving fra Specly til denne branchen.")

    def config_files(self):
        repo = self.repo
        # Hver JSON-fil i config-mappen leses, så en fil som ikke er gyldig JSON, meldes.
        for path in sorted(repo.config_dir.glob("*.json")) if repo.config_dir.is_dir() else []:
            ok, data = repo.json_of(path)
            if not ok:
                continue
            file = repo.rel(path)
            if path.name in SETTING_FILES:
                self.setting_file(file, path.name, data)
            elif path.name in REGISTRY_FILES and repo.registry_path(path.name) == path:
                self.registry_file(file, path.name, data)
        # Kildesystemene på en annen plass enn config-mappen, eller som YAML.
        ok, data = repo.registry_data(repo.source_systems_path) if repo.source_systems_path != repo.config_dir / "source_systems.json" else (False, None)
        if ok:
            self.registry_file(repo.rel(repo.source_systems_path), "source_systems.json", data)
        schemas = self.repo.root / ".specly/schemas"
        for name, schema_name in CONFIG_SCHEMAS.items():
            path = self.repo.config_dir / name
            schema = self.repo.read_json(schemas / schema_name, None)
            items = self.repo.read_json(path, None)
            if schema is None or not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                for pointer, code, message in validate(item, schema, schema, f"/{index}"):
                    level = self.f.warning if code == "schema.additionalProperties" else self.f.error
                    level(self.repo.rel(path), 1, code, f"{pointer}: {message}. Rett oppføringen så den følger .specly/schemas/{schema_name}.")
        concept_schema = self.repo.read_json(schemas / "concept.schema.json", None)
        for concept in self.repo.concepts if concept_schema else []:
            # Skjemaet sier at regelfiltrene er tekst. Specly skriver dem som lister og leser begge.
            data = dict(concept.data)
            data["rules"] = [
                {k: (json.dumps(v) if k in UUID_LIST_FILTERS and isinstance(v, list) else v) for k, v in rule.items()} if isinstance(rule, dict) else rule
                for rule in as_list(data.get("rules"))
            ]
            for pointer, code, message in validate(data, concept_schema, concept_schema, ""):
                (self.f.warning if code == "schema.additionalProperties" else self.f.error)(concept.file, concept.first_line + 1, code, f"{pointer or '/'}: {message}. Rett begrepsfilen så den følger .specly/schemas/concept.schema.json.")

    def setting_file(self, file, name, data):
        """odcs.json, table_naming.json og status_lists.json slik Specly leser dem."""
        if not isinstance(data, dict):
            self.f.error(file, 1, "config.unreadable", f"Filen skal være et JSON-objekt, men er {kind_of(data)}. Specly kan ikke lese den. Rett filen.")
            return
        if name != "status_lists.json":
            return
        levels = ("table", "column", "diagram", "dataProduct")
        uses = {}
        for level, source in data.items():
            if level not in levels:
                self.f.error(file, 1, "config.unreadable", f"{level} er ikke et nivå. Gyldige nivåer er {', '.join(levels)}. Specly kan ikke lese filen. Rett den.")
                return
            if source is None:
                continue
            if source not in levels:
                self.f.error(file, 1, "config.unreadable", f"{level} bruker listen til {source}, som ikke er et nivå. Gyldige nivåer er {', '.join(levels)}. Specly kan ikke lese filen. Rett den.")
                return
            if source == level:
                self.f.error(file, 1, "config.unreadable", f"{level} kan ikke bruke sin egen liste. Skriv null der. Specly kan ikke lese filen.")
                return
            uses[level] = source
        for level, source in uses.items():
            if source in uses:
                self.f.error(file, 1, "config.unreadable", f"{level} bruker listen til {source}, som selv bruker et annet nivås liste. Specly kan ikke lese filen. La {level} peke på et nivå med egen liste.")
                return

    def registry_file(self, file, name, data):
        """En registerfil slik Specly leser den: første brudd gjør hele filen uleselig."""

        def bad(index, message):
            self.broken_registries.add(name)
            self.f.error(file, 1, "config.unreadable", f"/{index}: {message} Specly kan da ikke lese filen, og ingenting fra den tas inn. Rett oppføringen.")

        if not isinstance(data, list):
            self.broken_registries.add(name)
            self.f.error(file, 1, "config.unreadable", f"Filen skal være en liste, men er {kind_of(data)}. Specly kan ikke lese den. Rett filen.")
            return
        text = lambda item, key, limit=512: isinstance(item.get(key), str) and len(item[key].encode("utf-16-le")) // 2 <= limit
        seen = {}
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                return bad(index, f"Oppføringen skal være et JSON-objekt, men er {kind_of(item)}.")
            uuid = item.get("uuid")
            if uuid is not None and not (isinstance(uuid, str) and UUID.match(uuid)):
                return bad(index, f"uuid er {uuid}, som ikke er en uuid. Bruk en uuid v4, eller ta bort uuid på en ny oppføring (Specly lager en).")
            if name == "flag_rules.json":
                if not (item.get("flagUuid") is None and isinstance(item.get("flag"), str) and item["flag"]) and not (isinstance(item.get("flagUuid"), str) and UUID.match(item["flagUuid"])):
                    return bad(index, "Regelen må ha flag (flaggets navn) eller flagUuid (en uuid).")
                if not text(item, "matchMode") or item["matchMode"] not in MATCH_MODES:
                    return bad(index, f"matchMode skal være en av {', '.join(MATCH_MODES)}.")
                if not text(item, "pattern") or not item["pattern"]:
                    return bad(index, "pattern mangler eller er tom.")
                if item.get("tableNamePattern") is not None and not text(item, "tableNamePattern"):
                    return bad(index, "tableNamePattern skal være tekst.")
                if item.get("isActive") is not None and not isinstance(item["isActive"], bool):
                    return bad(index, "isActive skal være true eller false.")
                if item.get("order") is not None and not is_number(item["order"]):
                    return bad(index, "order skal være et tall.")
            elif name == "metadata_field_definitions.json":
                if not text(item, "label"):
                    return bad(index, "label mangler eller er ikke tekst.")
                level = {"tabell": "tableType", "kolonne": "column", "beregning": "column"}.get(item.get("fieldType"))
                if level and entity_types(item) != [level]:
                    return bad(index, f"Et felt av typen {item.get('fieldType')} må ha entityTypes [\"{level}\"].")
            elif not text(item, "name", 16384 if name == "datatypes.json" else 512):
                return bad(index, "name mangler eller er ikke tekst.")
            if isinstance(uuid, str):
                if uuid.lower() in seen:
                    self.f.error(file, 1, "lint.uuid.duplicate", f"/{index} har samme uuid som /{seen[uuid.lower()]}. Specly leser da ingen av dem. Gi den ene en ny uuid v4, eller ta bort uuid på den nye oppføringen.")
                seen.setdefault(uuid.lower(), index)
        if name == "flags.json":
            named = {}
            for index, item in enumerate(data):
                if isinstance(item.get("name"), str):
                    if item["name"] in named:
                        self.f.warning(file, 1, "lint.flag.duplicateName", f"/{index} har samme navn som /{named[item['name']]} ({item['name']}). En tagg med det navnet er bare ett av flaggene (det siste), så reglene og kolonnene kan få et annet flagg enn ventet. Gi flaggene hvert sitt navn.")
                    named.setdefault(item["name"], index)
        if name == "metadata_field_definitions.json":
            reserved = set()
            for index, item in enumerate(data):
                key = item.get("key")
                if key not in ("description", "developerNote"):
                    continue
                types = entity_types(item)
                if "column" in types and types != ["column"]:
                    return bad(index, f"{key} er et innebygd kolonnefelt (entityTypes må være [\"column\"]). Et eget felt kan ikke bruke den nøkkelen.")
                if types == ["column"]:
                    if key in reserved:
                        return bad(index, f"{key} er et innebygd kolonnefelt og er definert to ganger.")
                    reserved.add(key)

    def datatypes(self):
        """Navnene i datatypes.json. `None` når filen finnes, men ikke kan leses (meldt for seg)."""
        entries = self.registry("datatypes.json")
        if entries is None:
            return None if self.repo.datatypes_path.is_file() else Names([])
        return Names(str(e.get("name")) for e in entries)

    def builtin_values(self, file, node, what, line, builtins):
        """Innebygde tekstverdier Specly leser: av feil slag leses de som tomme, og i feil sted leses de ikke."""
        settings = self.repo.settings
        for builtin in builtins:
            value = settings.downstream_name(node) if builtin == "downstreamName" else settings.value(node, builtin)
            if value is not None and not isinstance(value, str):
                self.f.warning(file, line_of(node, "customProperties", line), "lint.value.type", f"{what} har {builtin} som er {kind_of(value)}, ikke tekst. Specly leser den som tom.{' En tabell uten type viser ingen av feltene som hører til typen: de tas ikke inn, hverken på tabellen eller på kolonnene.' if builtin == 'tableType' else ''} Skriv den som tekst (i anførselstegn).")
            target = settings.target(builtin)
            if target in SLOT_TARGETS and custom_properties(node).get(builtin) not in (None, ""):
                self.f.warning(file, line_of(node, "customProperties", line), "lint.value.place", f"{what} har {builtin} i customProperties, men Specly leser den fra {target} og leser denne som tom. Flytt verdien dit.")

    def table_names(self):
        seen = {}
        for table in self.repo.tables:
            key = (table.database.lower(), table.schema.lower(), table.name.lower())
            if table.ghost:
                continue
            if key in seen:
                self.f.error(table.file, table.line, "lint.table.duplicateName", f"Tabellen {table.name} finnes også i {seen[key].file}. Specly leser bare én kontrakt per tabellnavn. Slett den ene filen.", [seen[key].file])
            else:
                seen[key] = table

    def table(self, table, datatypes):
        if not table.name:
            self.f.error(table.file, table.line, "lint.table.noName", "Tabellen mangler name. Legg til name.")
        self.id(table.file, table.obj, table.line, f"Tabellen {table.name}")
        settings = self.repo.settings
        # Rot-`status` i en kontrakt med flere tabeller er dataproduktets, ikke tabellens.
        at_root = settings.target("tableStatus") == "status"
        if not at_root or len(as_list(table.contract.get("schema"))) == 1:
            node = table.contract if at_root else table.obj
            self.status(table.file, line_of(node, "status" if at_root else "customProperties", table.line), f"Tabellen {table.name}", settings.value(node, "tableStatus"), "table_statuses.json")
        single = len(as_list(table.contract.get("schema"))) == 1 and "speclyId" not in custom_properties(table.contract)
        root_status = table.contract.get("status")
        if single and settings.target("tableStatus") == "customProperties" and isinstance(root_status, str) and root_status:
            self.f.warning(table.file, line_of(table.contract, "status", table.line), "lint.value.place", f"Tabellen {table.name} har status {root_status} ved roten, men Specly leser tabellstatusen fra {settings.target('tableStatus')} ({settings.property('tableStatus')}) og leser denne som tom. Flytt verdien dit.")
        self.builtin_values(table.file, table.obj, f"Tabellen {table.name}", table.line, ("tableType", "sourceSystem", "databaseName", "schemaName"))
        for builtin, known, registry, rule, what in (
            ("tableType", self.table_types, "table_types.json", "lint.enum.tableType", "tabelltypen"),
            ("sourceSystem", self.source_systems, "source_systems.json", "lint.enum.sourceSystem", "kildesystemet"),
        ):
            value = settings.value(table.obj, builtin)
            problem = known.problem(value) if known is not None and isinstance(value, str) and value else None
            if problem:
                registry_file = self.repo.rel(self.repo.registry_path(registry))
                if problem == "case":
                    self.f.error(table.file, line_of(table.obj, "customProperties", table.line), rule, f"Tabellen {table.name} har {what} {json.dumps(value, ensure_ascii=False)}, men {registry_file} har {known.like(value)} (andre store og små bokstaver eller mellomrom). Specly kjenner verdien bare slik den er skrevet, og lister tabellen som uleselig til det er rettet. Rett navnet; fix --add-values legger det ikke til.", self.enum_related(registry, value))
                else:
                    self.missing_value(registry, value, self.f.error(table.file, line_of(table.obj, "customProperties", table.line), rule, f"Tabellen {table.name} har {what} {value}, som ikke finnes i {registry_file}. «Hent fra Git» stopper på en verdi Specly ikke har, og repoet skal ha hver verdi kontraktene bruker. Legg verdien til der i samme push (fix --add-values gjør det), eller rett navnet.", self.enum_related(registry, value)))
        self.custom_entries(table.file, table.obj, f"Tabellen {table.name}", table.line)
        seen = {}
        for column in table.columns:
            prop = column.prop
            where = f"{table.name}.{column.name}"
            if not column.name:
                self.f.error(table.file, column.line, "lint.column.noName", f"En kolonne i {table.name} mangler name. Legg til name.")
            elif column.name.lower() in seen:
                self.f.error(table.file, column.line, "lint.column.duplicateName", f"{where} finnes to ganger i tabellen (store og små bokstaver regnes som like). Gi den ene et annet navn eller fjern den.")
            seen[column.name.lower()] = column
            self.id(table.file, prop, column.line, f"Kolonnen {where}")
            self.custom_entries(table.file, prop, f"Kolonnen {where}", column.line)
            exclude = settings.property("excludeFromSorting")
            if settings.target("excludeFromSorting") in (None, "customProperties") and exclude in custom_properties(prop):
                self.f.warning(table.file, line_of(prop, "customProperties", column.line), "lint.value.place", f"{where} har {exclude} i customProperties. Specly leser {exclude} bare på tabellen (unntaket fra kolonnesorteringen gjelder hele tabellen) og hopper over den på en kolonne, uten å si fra. Flytt den til tabellens customProperties, eller ta den bort.")
            for key in BOOLEANS:
                if prop.get(key) is not None and not isinstance(prop[key], bool):
                    self.f.warning(table.file, line_of(prop, key, column.line), "lint.value.type", f"{where} har {key} {prop[key]}. Specly leser bare true som satt (uten anførselstegn), så dette leses som ikke satt. Skriv true eller false.")
            for key in ("description", "physicalType"):
                if prop.get(key) is not None and not isinstance(prop[key], str):
                    self.f.warning(table.file, line_of(prop, key, column.line), "lint.value.type", f"{where} har {key} som er {kind_of(prop[key])}, ikke tekst. Specly leser den som tom. Skriv den som tekst (i anførselstegn).")
            datatype = prop.get("physicalType")
            problem = datatypes.problem(datatype) if datatypes is not None and isinstance(datatype, str) and datatype else None
            if problem == "case":
                datatypes_file = self.repo.rel(self.repo.datatypes_path)
                self.f.warning(table.file, line_of(prop, "physicalType", column.line), "lint.enum.dataType", f"{where} har datatypen {json.dumps(datatype, ensure_ascii=False)}, men {datatypes_file} har {datatypes.like(datatype)} (andre store og små bokstaver eller mellomrom), sannsynligvis en skrivefeil. Specly kjenner en datatype bare slik den er skrevet: «Fra Git» ber om en type for kolonnen («Trenger type») før den kan tas inn. Rett navnet; fix --add-values legger det ikke til.", self.enum_related("datatypes.json", datatype))
            elif problem:
                datatypes_file = self.repo.rel(self.repo.datatypes_path)
                self.missing_value("datatypes.json", datatype, self.f.warning(table.file, line_of(prop, "physicalType", column.line), "lint.enum.dataType", f"{where} har datatypen {datatype}, som ikke finnes i {datatypes_file}. Finnes den heller ikke i Specly, ber «Fra Git» om en type for kolonnen («Trenger type») før den kan tas inn. Legg datatypen til der i samme push (fix --add-values gjør det), eller rett navnet.", self.enum_related("datatypes.json", datatype)))
            if not str(prop.get("description") or "").strip():
                self.f.warning(table.file, column.line, NO_DESCRIPTION, f"{where} mangler description.")
            self.status(table.file, column.line, f"Kolonnen {where}", settings.value(prop, "columnStatus"), "column_statuses.json")
            self.builtin_values(table.file, prop, f"Kolonnen {where}", column.line, ("columnStatus", "downstreamName", "developerNote"))
            tags = as_list(prop.get("tags"))
            for index, tag in enumerate(tags if self.flags is not None else []):
                problem = self.flags.problem(tag) if isinstance(tag, str) else None
                if problem:
                    flags_file = self.repo.rel(self.repo.config_dir / "flags.json")
                    if problem == "case":
                        self.f.error(table.file, line_of(tags, index, column.line), "lint.enum.flag", f"{where} har taggen {json.dumps(tag, ensure_ascii=False)}, men {flags_file} har flagget {self.flags.like(tag)} (andre store og små bokstaver eller mellomrom). Specly kjenner et flagg bare slik det er skrevet, og lister kolonnen som uleselig til det er rettet. Rett navnet; fix --add-values legger det ikke til.", self.enum_related("flags.json", tag))
                    else:
                        self.missing_value("flags.json", tag, self.f.error(table.file, line_of(tags, index, column.line), "lint.enum.flag", f"{where} har taggen {tag}, som ikke er et flagg i {flags_file}. «Hent fra Git» stopper på et flagg Specly ikke har, og repoet skal ha hvert flagg kontraktene bruker. Legg flagget til der i samme push (fix --add-values gjør det), eller rett navnet.", self.enum_related("flags.json", tag)))
            sources = self.lineage(table, column)
            if not sources and any(table.name.startswith(prefix) for prefix in self.lineage_required):
                self.f.warning(table.file, column.line, "lint.column.noLineage", f"{where} har ingen kilde ({self.lineage_key()}).")
            for index, rel in enumerate(as_list(prop.get("relationships"))):
                self.relation_read(table.file, rel, line_of(as_list(prop.get("relationships")), index, column.line), f"Relasjonen fra {where}", True)
                self.relation_id(table.file, rel, line_of(as_list(prop.get("relationships")), index, column.line), f"fra {where}")
                targets = as_map(rel).get("to")
                for target in targets if isinstance(targets, list) else [targets]:
                    self.reference(table.file, line_of(as_list(prop.get("relationships")), index, column.line), "lint.relation.dangling", f"Relasjonen fra {where}", target)
            self.quality(table, as_list(prop.get("quality")), where, column.line)
        relationships = as_list(table.obj.get("relationships"))
        for index, rel in enumerate(relationships):
            self.relation_read(table.file, rel, line_of(relationships, index, table.line), f"Relasjonen i {table.name}", False)
            self.relation_id(table.file, rel, line_of(relationships, index, table.line), f"i {table.name}")
            for side in ("from", "to"):
                targets = as_map(rel).get(side)
                for target in targets if isinstance(targets, list) else [targets]:
                    self.reference(table.file, line_of(relationships, index, table.line), "lint.relation.dangling", f"Relasjonen i {table.name}", target)
        self.quality(table, as_list(table.obj.get("quality")), table.name, table.line)
        names = {}
        for scope in [table.obj] + [c.prop for c in table.columns]:
            rules = as_list(scope.get("quality"))
            for index, rule in enumerate(rules):
                name = as_map(rule).get("name")
                if isinstance(name, str) and name:
                    if name.lower() in names:
                        self.f.warning(table.file, line_of(rules, index, table.line), "lint.quality.duplicateName", f"Kvalitetsregelen {name} finnes mer enn én gang i {table.name} (store og små bokstaver regnes som like). Specly leser regelen inn som den er, men navnet blir navnet på DLT-expectation og må være unikt per tabell. Gi regelen et eget navn.")
                    names[name.lower()] = True

    def custom_entries(self, file, node, what, fallback_line):
        """En oppføring i customProperties uten `property` eller `value` hopper Specly over."""
        entries = as_list(node.get("customProperties"))
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            missing = "property" if entry.get("property") is None else "value" if "value" not in entry else None
            if missing:
                shown = f" ({entry.get('property')})" if missing == "value" else ""
                self.f.warning(file, line_of(entries, index, fallback_line), "lint.customProperty.incomplete", f"{what} har en oppføring i customProperties{shown} uten {missing}. Specly hopper over den, og verdien leses som ikke satt. Skriv både property og value.")

    def relation_read(self, file, rel, line, what, on_column):
        """En relasjon Specly hopper over når den leser."""
        if not isinstance(rel, dict):
            return
        kind = rel.get("type")
        if isinstance(kind, str) and kind != "foreignKey":
            self.f.warning(file, line, "lint.relation.skipped", f"{what} har type {kind}. Specly leser bare foreignKey og hopper over denne, så relasjonen leses som fjernet. Skriv type: foreignKey.")
        elif "to" not in rel:
            self.f.warning(file, line, "lint.relation.skipped", f"{what} mangler to. Specly hopper over den, så relasjonen leses som fjernet. Legg til to: tabell.kolonne.")
        elif not on_column and "from" not in rel:
            self.f.warning(file, line, "lint.relation.skipped", f"{what} mangler from. Specly hopper over den, så relasjonen leses som fjernet. Legg til from: tabell.kolonne.")

    def relation_id(self, file, rel, line, where):
        rel_id = as_map(rel).get("id")
        if isinstance(rel_id, str) and rel_id:
            group = self.relations_by_id.setdefault(rel_id.lower(), [])
            if all(f != file for f, _, _ in group):
                group.append((file, line_of(rel, "id", line), where))

    def status(self, file, line, what, value, registry):
        allowed = self.statuses[registry]
        problem = allowed.problem(value) if allowed is not None and isinstance(value, str) and value else None
        if problem:
            registry_file = self.repo.rel(self.repo.config_dir / registry)
            if problem == "case":
                self.f.error(file, line, "lint.enum.status", f"{what} har status {json.dumps(value, ensure_ascii=False)}, men {registry_file} har {allowed.like(value)} (andre store og små bokstaver eller mellomrom). Specly kjenner en status bare slik den er skrevet, og lister tabellen som uleselig til det er rettet. Rett navnet; fix --add-values legger det ikke til.", self.enum_related(self.status_files[registry], value))
            else:
                self.missing_value(self.status_files[registry], value, self.f.error(file, line, "lint.enum.status", f"{what} har status {value}, som ikke finnes i {registry_file}. «Hent fra Git» stopper på en status Specly ikke har, og repoet skal ha hver status kontraktene bruker. Legg statusen til der i samme push (fix --add-values gjør det), eller rett navnet.", self.enum_related(self.status_files[registry], value)))

    def missing_value(self, registry, name, item):
        self.missing_values.setdefault(registry, {}).setdefault(name, []).append(item)

    def lineage_key(self):
        s = self.repo.settings
        if as_map(s.mappings.get("upstreamColumns")).get("odcsTarget") == "transformSourceObjects":
            return "transformSourceObjects"
        return s.property("upstreamColumns")

    def lineage(self, table, column):
        """Sjekker kolonnens kilder og gir dem tilbake."""
        prop = column.prop
        where = f"{table.name}.{column.name}"
        custom_name = self.repo.settings.property("upstreamColumns")
        custom = custom_properties(prop).get(custom_name)
        slot = as_list(prop.get("transformSourceObjects"))
        entries = []
        for entry in as_list(custom):
            if isinstance(entry, dict) and "sourceTable" in entry:
                entries.append((f"{entry.get('sourceTable')}.{entry.get('sourceColumn')}", line_of(prop, "customProperties", column.line)))
            elif isinstance(entry, dict):
                entries.append((entry.get("column"), line_of(prop, "customProperties", column.line)))
            else:
                entries.append((entry, line_of(prop, "customProperties", column.line)))
        # En eldre eksport skrev bare kildetabellene i transformSourceObjects
        # og selve lenkene i custom property-en.
        if not entries:
            entries = [(entry, line_of(slot, index, column.line)) for index, entry in enumerate(slot)]
        counts = {}
        for reference, line in entries:
            if isinstance(reference, str):
                counts[reference.lower()] = counts.get(reference.lower(), 0) + 1
        for reference, line in entries:
            if isinstance(reference, str) and counts.get(reference.lower(), 0) > 1:
                counts[reference.lower()] = 0
                self.f.warning(table.file, line, "lint.lineage.duplicate", f"{where} har kilden {reference} flere ganger. Specly leser hver oppføring som en egen kilde, så kolonnen får like kilder. Fjern de like.")
        if self.lint_rules.get("lineageTargetMustExist") is False:
            return entries
        for reference, line in entries:
            self.reference(table.file, line, "lint.lineage.dangling", f"Kilden til {where}", reference)
        return entries

    def reference(self, file, line, rule, what, reference):
        if reference is None:
            return
        if not isinstance(reference, str):
            self.f.error(file, line, rule, f"{what} er ikke en tekst på formen tabell.kolonne. Rett referansen.")
            return
        table, column, missing = self.repo.resolve(reference)
        if missing is None:
            return
        parts = split_reference(reference)
        related = [table.file] if table else []
        b = self.baseline
        if missing == "format":
            self.f.error(file, line, rule, f"{what} peker på {reference}, som ikke er på formen tabell.kolonne. Rett referansen.")
        elif missing == "ambiguous":
            self.f.error(file, line, "lint.name.ambiguous", f"{what} peker på {reference}, men flere tabeller heter {parts[-2]}. Skriv referansen som database.skjema.tabell.kolonne.", [t.file for t in self.repo.by_name.get(parts[-2].lower(), [])])
        elif missing == "table":
            renamed = b.table_renames.get(parts[-2].lower()) if b else None
            related = b.files_of(b.old_table_files, parts[-2]) if b else []
            hint = f"Tabellen heter nå {renamed}. Oppdater referansen." if renamed else "Fjern referansen eller legg tabellen tilbake."
            self.f.error(file, line, rule, f"{what} peker på {reference}, men tabellen {parts[-2]} finnes ikke. {hint}", related)
        else:
            renamed = self.baseline.column_renames.get((table.name.lower(), parts[-1].lower())) if self.baseline else None
            hint = f"Kolonnen heter nå {renamed}. Oppdater referansen." if renamed else "Fjern referansen eller legg kolonnen tilbake."
            self.f.error(file, line, rule, f"{what} peker på {reference}, men kolonnen {parts[-1]} finnes ikke i {table.name}. {hint}", related)

    def quality(self, table, rules, where, fallback_line):
        seen = self.rule_ids.setdefault(table.file, {})
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            line = line_of(rules, index, fallback_line)
            rule_id = rule.get("id")
            if isinstance(rule_id, str) and rule_id:
                if rule_id.lower() in seen:
                    self.f.error(table.file, line_of(rule, "id", line), "lint.quality.duplicateId", f"Kvalitetsregelen {rule.get('name') or index + 1} på {where} har samme id som regelen på linje {seen[rule_id.lower()]} i filen. Specly kjenner en regel på id-en: den ene tas ikke med, og rekkefølgen på reglene endres. Gi regelen en ny uuid v4.")
                else:
                    seen[rule_id.lower()] = line_of(rule, "id", line)
                    self.rules_by_id.setdefault(rule_id.lower(), []).append((table.file, seen[rule_id.lower()], (rule.get("name") or index + 1, where)))
            for key in OPERATORS:
                number_line = line_of(rule, key, line)
                lines = self.repo.read_text(self.repo.top / table.file) if rule.get(key) is not None and not isinstance(rule.get(key), (bool, list, dict)) else None
                raw = re.sub(r"\s+#.*$", "", lines.split("\n")[number_line - 1].split(":", 1)[-1].strip()) if lines and 0 < number_line <= lines.count("\n") + 1 else ""
                if digits_but_not_number(raw):
                    self.f.warning(table.file, number_line, "lint.value.text", f"Kvalitetsregelen {rule.get('name') or index + 1} på {where} har {key} {raw}. Specly leser det som teksten {raw}, ikke som tallet. Skriv tallet uten ledende nuller.")
            name = rule.get("name")
            if isinstance(name, str) and name and not RULE_NAME.match(name):
                self.f.warning(table.file, line, "lint.quality.invalidName", f"Kvalitetsregelen {name} på {where} har et ugyldig navn. Specly leser regelen inn som den er, men navnet blir navnet på DLT-expectation og kan bare inneholde a-z, 0-9 og _. Gi regelen et gyldig navn.")
            for key, allowed, code in (("dimension", DIMENSIONS, "lint.quality.dimension"), ("metric", METRICS, "lint.quality.metric")):
                value = rule.get(key)
                if value is not None and value not in allowed:
                    self.f.warning(table.file, line_of(rule, key, line), code, f"Kvalitetsregelen {name or index + 1} på {where} har {key} {value}. Specly leser verdien inn som den står, men ODCS kjenner bare {', '.join(allowed)}.")
            kind = rule.get("type")
            operator = any(key in rule for key in OPERATORS)
            filled = lambda key: isinstance(rule.get(key), str) and rule[key] != ""
            read_as = (
                "sql"
                if kind == "sql" and filled("query") and operator
                else "library"
                if isinstance(rule.get("metric"), str) and operator
                else "custom"
                if kind == "custom" and filled("engine") and filled("implementation")
                else "text"
            )
            if isinstance(kind, str) and kind != "text" and read_as == "text":
                needs = {"sql": "query og en operator (for eksempel mustBe)", "custom": "engine og implementation"}.get(kind, "metric og en operator (for eksempel mustBe)")
                known = "" if kind in ("library", "sql", "custom") else f" Specly kjenner typene library, sql, custom og text, ikke {kind}."
                self.f.warning(table.file, line_of(rule, "type", line), "lint.quality.readAsText", f"Kvalitetsregelen {name or index + 1} på {where} har type {kind}, men Specly leser den som en ren tekstregel: operator, metric og query tas ikke inn.{known} En regel av typen {kind if not known else 'library'} trenger {needs}.")
            severity = rule.get("severity")
            if severity is not None and not isinstance(severity, str):
                self.f.warning(table.file, line_of(rule, "severity", line), "lint.quality.severity", f"Kvalitetsregelen {name or index + 1} på {where} har en severity som ikke er tekst. Specly leser den som tom. Skriv den som tekst.")

    def id(self, file, node, line, what):
        raw = node.get("id")
        if raw is None:
            if not self.repo.settings.shorthand:
                self.f.warning(file, line, "lint.uuid.missing", f"{what} mangler id. Specly kjenner den da på navnet, og ingen eksport skriver id-en inn: får den nytt navn i Git, blir det en ny, og det Specly hadde på den gamle følger ikke med. Gi den en id: fix --add-ids --changed-from <base> skriver den Specly selv ville laget (i et repo uten commits holder fix --add-ids).")
        elif not isinstance(raw, str) or not UUID.match(raw):
            self.f.warning(file, line_of(node, "id", line), "lint.uuid.invalid", f"{what} har id {raw}, som ikke er en uuid. Specly leser id-en som den står, men en id som ikke er en uuid v4 er lett å få til å støte mot en annen. Bruk en uuid v4 (for eksempel fra uuidgen).")

    def original_file(self, files):
        """Filen som hadde id-en fra før, eller `None` når Git ikke sier hvilken: den Specly har skrevet
        (`.specly/files.json`), og med `--changed-from` den som ikke er endret siden."""
        left = sorted(set(files))
        left = [f for f in left if f in self.exported] or left
        if self.baseline:
            left = [f for f in left if f not in self.baseline.changed] or left
        return left[0] if len(left) == 1 else None

    def copied_id(self, holders, noun, held=""):
        """Samme id flere steder (`holders`: fil, linje, navnet først i meldingen, navnet som den andre). Feilen står
        på kopien. Sier ikke Git hvilken som er kopien, står den på alle, og ingen av dem kalles ny: den som gir
        originalen en ny id, får den lest som slettet og laget på nytt."""
        if len(holders) < 2:
            return
        original = self.original_file([file for file, *_ in holders])
        kept = next((h for h in holders if h[0] == original), None)
        for holder in holders:
            file, line, subject, _ = holder
            if holder is kept:
                continue
            other_file, _, _, other = kept or next(h for h in holders if h is not holder)
            same = f"{subject} har samme id som {other} i {other_file}"
            if kept and other_file != file:
                message = f"{same}, som hadde id-en fra før. {held}La id-en stå der, og gi {noun} her en ny uuid v4."
            elif kept:
                message = f"{same}. {held}Gi den ene en ny uuid v4."
            else:
                message = f"{same}. {held}Den ene er en kopi: gi kopien en ny uuid v4, og la id-en stå der den sto først. Får originalen en ny id, leser Specly det som at {noun} er slettet og en ny laget."
            self.f.error(file, line, "lint.uuid.duplicate", message, [other_file])

    def ids(self):
        tables = {}
        for table in self.repo.tables:
            if table.id:
                tables.setdefault(table.id.lower(), []).append((table.file, table.line, f"Tabellen {table.name}", table.name))
        for holders in tables.values():
            self.copied_id(holders, "tabellen")
        for columns in self.repo.columns_by_id.values():
            self.copied_id([(c.table.file, c.line, f"Kolonnen {c.table.name}.{c.name}", f"{c.table.name}.{c.name}") for c in columns], "kolonnen")
        # Hver id under en kontrakt er unik i prosjektet: v3-innlesingen holder kontrakten med kopien tilbake.
        for holders in self.rules_by_id.values():
            self.copied_id([(file, line, f"Kvalitetsregelen {name} på {where}", f"regelen på {where}") for file, line, (name, where) in holders], "regelen", "Specly henter ikke inn kontrakten med kopien før dette er rettet. ")
        for holders in self.relations_by_id.values():
            self.copied_id([(file, line, f"Relasjonen {where}", f"relasjonen {where}") for file, line, where in holders], "relasjonen", "Specly henter ikke inn kontrakten med kopien før dette er rettet. ")
        if not self.baseline or self.lint_rules.get("rejectFabricatedUuids") is False:
            return
        for table in self.repo.tables:
            old = self.baseline.old_columns.get((table.id or table.name).lower(), {})
            for column in table.columns:
                old_id = old.get(column.name)
                if old_id and column.id and old_id.lower() != column.id.lower() and old_id.lower() not in self.repo.columns_by_id:
                    self.f.error(table.file, line_of(column.prop, "id", column.line), "lint.uuid.fabricated", f"Kolonnen {table.name}.{column.name} har fått ny id, men er ikke en ny kolonne. Specly ville lest den som en sletting og en ny kolonne. Sett id tilbake til {old_id}.")

    def concepts(self):
        for file, line, message in self.repo.concept_problems:
            self.f.error(file, line, "concept.unreadable", message)
        by_uuid = {}
        for concept in self.repo.concepts:
            file, data, first_line = concept.file, concept.data, concept.first_line
            shape = Shape()
            shape.key(data, "name", "", "text")
            shape.key(data, "uuid", "", "text")
            links = shape.key(data, "columns", "", "list")
            shape.maps(data, "rules", "")
            for index, entry in enumerate(links or []):
                if shape.problem is None and not isinstance(entry, str) and not (isinstance(entry, dict) and isinstance(entry.get("path"), str)):
                    shape.problem = (line_of(links, index), f"columns[{index}] skal være en sti (tabell.kolonne) eller en oppføring med path, men er {kind_of(entry)}. Specly kan ikke lese filen før det er rettet.")
            if shape.problem:
                self.f.error(file, shape.problem[0] + first_line, "concept.unreadable", shape.problem[1])
                self.bad_concepts.add(file)
                continue
            uuid = data.get("uuid")
            if isinstance(uuid, str) and uuid:
                by_uuid.setdefault(uuid.lower(), []).append((file, line_of(data, "uuid") + first_line))
                if not UUID.match(uuid):
                    self.f.warning(file, line_of(data, "uuid") + first_line, "lint.uuid.invalid", f"Begrepet {concept.name} har uuid {uuid}, som ikke er en uuid. Specly kjenner begrepet på uuid: en endret uuid leses som at begrepet er slettet og et nytt laget. Sett den tilbake, eller bruk en uuid v4 på et nytt begrep.")
            columns = as_list(data.get("columns"))
            seen = set()
            for index, entry in enumerate(columns):
                line = line_of(columns, index) + first_line
                path = entry.get("path") if isinstance(entry, dict) else entry
                if not isinstance(path, str):
                    continue
                if path in seen:
                    self.f.error(file, line, "lint.concept.duplicateLink", f"{path} er lenket to ganger. Fjern den ene lenken.")
                seen.add(path)
                column_id = entry.get("columnUuid") if isinstance(entry, dict) else None
                if isinstance(column_id, str) and column_id.lower() in self.repo.columns_by_id:
                    continue
                self.reference(file, line, "lint.concept.danglingColumn", "Lenken", path)
        self.same_uuid(by_uuid, "Begrepet", "Gi det nye begrepet en ny uuid v4, eller ta bort uuid (Specly lager en).")

    # ---------- Begrepslenker: det «Bruk reglene» og neste eksport skriver ----------
    #
    # Specly regner lenkene ut slik (concept_inheritance.rs, business_concept.rs):
    # en kolonne en regel treffer og som ikke har en lenke, får en ny lenke.
    # Den får et unntak for hvert tekstfelt der kolonnen har egen tekst som
    # ikke er begrepets (eller begrepet har ingen), og for `dataType` når
    # kolonnens datatype ikke er begrepets (eller begrepet har ingen). Uten
    # unntak er lenken regelens og står ikke i begrepsfilen; med unntak skrives
    # den der. Hvert felt uten unntak der kolonnen er tom, får begrepets tekst.
    # Sjekken antar det «Bruk reglene» gjør uten valg: alle begreper, «Behold
    # egen tekst», ikke «Sett datatype fra begrepet», og at Specly ikke har
    # flere lenker enn dem Git har (en vanlig regellenke står bare i Specly).

    def concept_links(self):
        repo = self.repo
        listed = {}
        unknown = set()
        concepts = [c for c in repo.concepts if c.file not in self.bad_concepts]
        for concept in concepts:
            for entry in as_list(concept.data.get("columns")):
                path = entry.get("path") if isinstance(entry, dict) else entry
                column_id = entry.get("columnUuid") if isinstance(entry, dict) else None
                column = (repo.columns_by_id.get(column_id.lower()) or [None])[0] if isinstance(column_id, str) else None
                column = column or (repo.resolve(path)[1] if isinstance(path, str) else None)
                if column is None:
                    # En lenke sjekken ikke finner kolonnen til (meldt som en feil): ingen dom over kolonnene den kan gjelde.
                    parts = split_reference(path) if isinstance(path, str) else []
                    for table in repo.by_name.get(parts[-2].lower(), []) if len(parts) > 1 else []:
                        unknown.add(id(table.column(parts[-1])))
                    continue
                listed.setdefault(id(column), []).append((concept, entry))
        for concept in concepts:
            if not concept.has_uuid:
                item = self.f.warning(concept.file, 1, "lint.concept.noUuid", f"Begrepet {concept.name} har ingen uuid. Specly gir det uuid {concept.uuid} (laget av navnet), og neste eksport skriver den i filen. Skriv uuid: {concept.uuid} i toppen.")
                self.concept_uuids[concept.path] = (concept, concept.uuid, item)
        matcher = RuleMatcher(repo, concepts)
        for concept, rule, why in matcher.invalid:
            self.f.warning(concept.file, 1, "lint.concept.ruleRegex", f"Regelen med columnNamePattern {rule.get('columnNamePattern')!r} i {concept.name} bruker {why}. Specly leser mønstre med Rust sin regex, som ikke kan det: regelen treffer ingen kolonner i Specly, og sjekken regner den slik. Skriv mønsteret uten det.")
        glossary = self.glossary_fields()
        for table in repo.tables:
            if table.unreadable:
                continue
            shared = len(repo.by_name.get(table.name.lower(), [])) > 1
            for column in table.columns:
                if id(column) in unknown:
                    continue
                links = listed.get(id(column), [])
                excluded = {c.uuid for c, e in links if link_kind(e)[0] == "excluded"}
                linked = [(c, e) for c, e in links if link_kind(e)[0] != "excluded"]
                winner, rule, why = matcher.concept(column, own_texts(repo.settings, column)["downstreamName"], excluded) if matcher.rules else (None, None, None)
                if why:
                    self.undetermined(column, None, why)
                    continue
                if (linked or winner) and shared:
                    self.undetermined(column, (linked[-1][0] if linked else winner), f"tabellnavnet {table.name} finnes i flere kontrakter (store og små bokstaver regnes likt). Specly skriver da columnUuid på lenken, og hvilken tabell den mener, avgjør ikke sjekken")
                    continue
                if linked:
                    concept, entry = linked[-1]
                    source = link_kind(entry)[1]
                    if winner is not None and winner is not concept and source == "ruleBased":
                        self.undetermined(column, concept, f"en regel i {winner.name} treffer kolonnen først, og «Bruk reglene» flytter da lenken fra {concept.name} til {winner.name}")
                        continue
                    if winner is None and source == "ruleBased":
                        self.f.warning(column.table.file, column.line, "lint.concept.staleRuleLink", f"{column.table.name}.{column.name} står med source: ruleBased i {concept.file}, men ingen regel treffer kolonnen. {DEFAULTS_NOTE} sletter Specly lenken, og neste eksport tar den ut av {concept.file}. Skriv source: manual på lenken hvis den skal stå, eller ta den bort. (fix gjør ikke dette.)", [concept.file])
                    self.listed_link(concept, entry, column, glossary)
                elif winner is not None:
                    self.rule_link(winner, rule, column, glossary)

    def glossary_fields(self):
        """Kolonnefeltene en lenket kolonne arver i tillegg (glossaryLinkable), med navnene de kan stå under i en kontrakt."""
        out = []
        for entry in self.repo.registry("metadata_field_definitions.json") or []:
            # description og developerNote er kolonnens egne felt, ikke ekstra felt (RESERVED_COLUMN_KEYS).
            if entry.get("glossaryLinkable") is True and "column" in entity_types(entry) and isinstance(entry.get("key"), str) and entry["key"] not in ("description", "developerNote"):
                key = entry["key"]
                out.append((key, {key, entry.get("odcsPropertyName") or key, camel_case(key)}))
        return out

    def custom_held(self, concept, column, glossary):
        """Om kolonnen eller begrepet har verdi i et kolonnefelt som arves: da avgjør kolonnens tabelltype utfallet, og den står ikke i filene."""
        custom, meta = custom_properties(column.prop), as_map(concept.data.get("metadata"))
        held = [key for key, names in glossary if any(custom.get(n) not in (None, "") or meta.get(n) not in (None, "") for n in names)]
        if held:
            self.undetermined(column, concept, f"kolonnen eller {concept.name} har verdi i {', '.join(held)}, et kolonnefelt som arves, og om kolonnens tabelltype viser feltet, står ikke i filene")
        return bool(held)

    def undetermined(self, column, concept, why):
        self.f.warning(column.table.file, column.line, "lint.concept.undetermined", f"{column.table.name}.{column.name}: {why}. Hva neste eksport skriver om denne kolonnen og begrepet, avgjøres ikke av filene alene; sjekken gjetter ikke, og fix lar den stå.", [concept.file] if concept else [])

    def listed_link(self, concept, entry, column, glossary):
        """En lenke som står i begrepsfilen. Ved innlesing lager Specly den med unntakene i filen, og
        gir kolonnen begrepets tekst og datatype i hvert felt uten unntak. Bare på en kolonne Specly har
        fra før, legger den til et unntak for hvert tekstfelt pushen endrer (`column_texts`, `record_git_texts`)."""
        kind, source, exceptions = link_kind(entry)
        if self.custom_held(concept, column, glossary):
            return
        exceptions = [e for e in exceptions if isinstance(e, str)]
        own, data_type = own_texts(self.repo.settings, column), column_data_type(column)
        differ = [f for f in CONCEPT_TEXTS if f not in exceptions and own[f].strip() and own[f].strip() != concept.text[f].strip()]
        if "dataType" not in exceptions and data_type and concept.data_type and data_type != concept.data_type:
            differ.append("dataType")
        if differ:
            line = flow_entry({"exceptions": exceptions + differ, "link": "linkedWithExceptions", "path": link_path(column), **({"source": source} if source != "manual" else {})})
            history = self.baseline.column_history(column) if self.baseline else None
            if history == "new":
                self.f.warning(
                    column.table.file,
                    column.line,
                    "lint.concept.ownTextOverwritten",
                    f"{column.table.name}.{column.name} er ny i endringene og har egen verdi i {', '.join(differ)}, og {concept.file} lenker den til {concept.name} uten unntak for det. Ved innlesing skriver Specly begrepets verdi over kolonnens egen, og neste eksport skriver begrepets verdi i kontrakten. Skal kolonnen beholde sin egen, skriv lenken slik under columns i {concept.file}: {line}",
                    [concept.file],
                )
            elif isinstance(history, dict):
                old = own_texts(self.repo.settings, OldColumn(history))
                changed = [f for f in differ if f != "dataType" and old[f] != own[f]]
                rest = [f for f in differ if f not in changed]
                if changed:
                    self.f.warning(
                        column.table.file,
                        column.line,
                        "lint.concept.missingException",
                        f"{column.table.name}.{column.name} fikk ny egen verdi i {', '.join(changed)} i endringene, og {concept.file} lenker kolonnen til {concept.name} uten unntak for det. Specly lager da unntaket ved innlesing, og neste eksport endrer lenken. Skriv lenken slik under columns i {concept.file}: {line}",
                        [concept.file],
                    )
                if rest:
                    self.undetermined(column, concept, f"kolonnen har egen verdi i {', '.join(rest)} som endringene ikke rører, og {concept.file} lenker den uten unntak for det: om Specly beholder den eller skriver begrepets over, avhenger av hva Specly har nå. Skriv lenken slik for å være sikker: {line}")
            else:
                self.undetermined(column, concept, f"kolonnen har egen verdi i {', '.join(differ)}, og {concept.file} lenker den uten unntak for det. Specly lager unntaket bare på en kolonne den har fra før og når pushen endrer teksten; på en ny kolonne skriver den begrepets verdi over. Kjør check med --changed-from <base> for å få svar, eller skriv lenken slik: {line}")
        # Begrepets tekst i de tomme feltene: Specly gjør det på hver lenke den skriver.
        self.inherited(concept, column, own, exceptions + differ, f"er lenket til {concept.name} i {concept.file}, så", fixable=True)

    def rule_link(self, concept, rule, column, glossary):
        """En kolonne en regel lenker: lenken «Bruk reglene» lager, og om begrepsfilen må ha den."""
        own, data_type = own_texts(self.repo.settings, column), column_data_type(column)
        if self.custom_held(concept, column, glossary):
            return
        # En regel med filter treffer slik sjekken regner det, men det er ikke prøvd mot Specly: fix skriver ikke.
        filtered = any(filter_list(rule.get(key)) for key in UUID_LIST_FILTERS)
        note = " (Regelen har et filter: fix skriver ikke dette.)" if filtered else ""
        exceptions = [f for f in CONCEPT_TEXTS if own[f].strip() and (not concept.text[f].strip() or concept.text[f] != own[f])]
        if data_type and data_type != concept.data_type:
            exceptions.append("dataType")
        if exceptions:
            entry = {"exceptions": exceptions, "link": "linkedWithExceptions", "path": link_path(column), "source": "ruleBased"}
            reasons = ", ".join(
                f"dataType ({data_type}, begrepet har {concept.data_type or 'ingen'})" if f == "dataType" else f"{f} (kolonnen har egen tekst{'' if concept.text[f].strip() else ', begrepet har ingen'})"
                for f in exceptions
            )
            item = self.f.warning(
                column.table.file,
                column.line,
                "lint.concept.missingLink",
                f"En regel i {concept.name} treffer {column.table.name}.{column.name}. {DEFAULTS_NOTE} lenker Specly kolonnen med unntak for {reasons}, og neste eksport skriver lenken i {concept.file}. Skriv den der under columns: {flow_entry(entry)}{note}",
                [concept.file],
            )
            if not filtered:
                self.concept_writes.setdefault(concept.path, (concept, []))[1].append((entry, item))
        elif not data_type and concept.data_type:
            self.f.warning(column.table.file, column.line, "lint.concept.inheritedText", f"{column.table.name}.{column.name} har ingen datatype, og en regel i {concept.name} treffer den. {DEFAULTS_NOTE} gir Specly den datatypen {concept.data_type}, og neste eksport skriver den i kontrakten. Skriv physicalType: {concept.data_type} på kolonnen. (fix gjør ikke dette.)", [concept.file])
        self.inherited(concept, column, own, exceptions, f"treffes av en regel i {concept.name}. {DEFAULTS_NOTE} lenker Specly den, og", fixable=not filtered)

    def inherited(self, concept, column, own, exceptions, how, fixable):
        """Feltene kolonnen er tom i og arver: Specly fyller inn begrepets tekst, og neste eksport skriver den i kontrakten."""
        settings = self.repo.settings
        for field in CONCEPT_TEXTS:
            value = concept.text[field]
            if field in exceptions or own[field].strip() or not value.strip():
                continue
            key = text_slot(settings, field)
            if field == "downstreamName" and key == "businessName" and value == column.name:
                continue  # Specly skriver ikke en businessName lik kolonnens navn.
            # En nøkkel som står der (en businessName lik kolonnens navn), eller tekst med blanke på slutten av en linje
            # (som Speclys egen skriving ikke skriver som patchen gjør), skriver fix ikke.
            writes = fixable and key and key not in column.prop and not any(line != line.rstrip() for line in value.split("\n"))
            where = f"{key}: {json.dumps(value, ensure_ascii=False)}" if key else f"{field} (der innstillingene i odcs.json sender den)"
            item = self.f.warning(
                column.table.file,
                column.line,
                "lint.concept.inheritedText",
                f"{column.table.name}.{column.name} har ingen {field} og {how} Specly fyller inn begrepets tekst; neste eksport skriver den i kontrakten: {where}." + ("" if writes else " fix skriver ikke denne."),
                [concept.file],
            )
            if writes:
                self.column_texts.setdefault(self.repo.top / column.table.file, []).append((column, key, value, item))

    # ---------- Reglene i config-mappen: det de endrer hvis de kjøres i Specly ----------
    #
    # Reglene kjører aldri av seg selv i Specly: en bruker kjører dem (Specly tilbyr det etter
    # en innhenting). Sjekken regner ut det en kjøring over hele prosjektet ville endret, og
    # melder det neste eksport da skriver. Det filene alene ikke avgjør, meldes som
    # `undetermined`, og fix skriver det ikke.

    def column_flags(self, column):
        """Flaggene (uuid) Specly leser på kolonnen: taggene, og hver konstruksjonsplass som er true."""
        if self.flag_entries is None:
            self.flag_entries = self.registry("flags.json") or []
        flags = self.flag_entries
        if getattr(self, "flag_lookup", (None,))[0] is not flags:
            by_name = {str(f.get("name")): str(f.get("uuid")) for f in flags if f.get("uuid")}
            by_key = {f.get("systemKey"): str(f.get("uuid")) for f in flags if f.get("uuid") and f.get("systemKey")}
            self.flag_lookup = (flags, by_name, by_key, [u for u in by_name.values() if u.lower() in self.bound_flags()])
        _, by_name, by_key, bound = self.flag_lookup
        prop, settings = column.prop, self.repo.settings
        out = {by_name[t] for t in as_list(prop.get("tags")) if isinstance(t, str) and t in by_name}
        out |= {by_key[key] for key in BOOLEANS if prop.get(key) is True and key in by_key}
        # Et flagg odcs.json binder til en customProperties-oppføring, skriver eksporten der og ikke som tagg.
        out |= {u for u in bound if self.bound_flag_state(column, u)}
        if "businessKey" in by_key:
            target = settings.target("businessKey")
            name = settings.property("businessKey")
            if (target == "tags" and name in as_list(prop.get("tags"))) or (target in (None, "customProperties") and custom_properties(prop).get(name) in (True, "true")):
                out.add(by_key["businessKey"])
        return out - self.unknown_flags(column)

    def bound_flags(self):
        """Flaggene odcs.json binder til en kolonnes customProperties-oppføring (en definisjon med scope column og et blad
        med source {"kind": "flag"}): flagg-uuid -> [(oppføringens navn, nøklene ned til bladet, valueType)]. Eksporten
        skriver et slikt flagg i oppføringen, aldri som tagg (`binds`), og innhentingen leser det derfra."""
        if getattr(self, "flag_bindings", None) is None:
            self.flag_bindings = {}

            def walk(definition, nodes, path):
                for node in as_list(nodes):
                    if not isinstance(node, dict):
                        continue
                    key = node.get("key") if isinstance(node.get("key"), str) else ""
                    source = as_map(node.get("source"))
                    if "children" in node:
                        walk(definition, node.get("children"), path + [key])
                    elif source.get("kind") == "flag" and isinstance(source.get("uuid"), str):
                        self.flag_bindings.setdefault(source["uuid"].lower(), []).append((definition.get("name"), path + ([key] if key else []), definition.get("valueType")))

            for definition in as_list(self.repo.settings.odcs.get("customProperties")):
                if isinstance(definition, dict) and definition.get("scope") == "column" and isinstance(definition.get("name"), str):
                    walk(definition, definition.get("nodes"), [])
        return self.flag_bindings

    def bound_flag_state(self, column, uuid):
        """Om kolonnens customProperties-oppføring sier at den har det bundne flagget: `True`, `False`, eller `None` når
        sjekken ikke kan lese verdien (en form den ikke kjenner)."""
        entries = {e.get("property"): e.get("value") for e in as_list(column.prop.get("customProperties")) if isinstance(e, dict)}
        states = set()
        for name, path, value_type in self.bound_flags().get(uuid.lower(), []):
            if name not in entries:
                states.add(False)
                continue
            value = entries[name]
            if value_type == "list":
                value = True if isinstance(value, list) and any(v is True or v == "true" for v in value) else (False if isinstance(value, list) else None)
            else:
                for key in path if value_type == "object" else []:
                    value = value.get(key) if isinstance(value, dict) else None
            states.add(True if value is True or value == "true" else False if value in (None, False) else None)
        return True if True in states else None if None in states else False

    def unknown_flags(self, column):
        """Flaggene filene ikke avgjør om kolonnen har: med `primaryKeyRequired` er `required: true` på en primærnøkkel en del
        av nøkkelen, og innhentingen gir kolonnen flagget Påkrevd bare hvis Specly allerede har det (`required_flag_columns`)."""
        prop = column.prop
        if self.repo.settings.odcs.get("primaryKeyRequired") is False or prop.get("primaryKey") is not True or prop.get("required") is not True:
            return set()
        flags = self.flag_entries if self.flag_entries is not None else self.registry("flags.json") or []
        return {str(f.get("uuid")) for f in flags if f.get("uuid") and f.get("systemKey") == "required"}

    def renders(self, column, key):
        """Om Specly skriver nøkkelen `key` som kolonnen har i Git, når eksporten gjengir kolonnen (`build_property`): `True`,
        `False`, eller `None` når filene ikke avgjør det. Den nye nøkkelen et flagg gir, skriver eksporten foran den første av
        Speclys senere nøkler Git-filen har og Specly skriver (`next_key`), ellers sist i kolonnen."""
        prop, settings = column.prop, self.repo.settings
        value = prop.get(key)
        flags = self.flag_entries or []
        keys = {f.get("systemKey") for f in flags if f.get("systemKey")}
        mapped = lambda slot: any(as_map(m).get("odcsTarget") == slot for m in settings.mappings.values()) or any(
            e.get("odcsTarget") == slot and "column" in entity_types(e) for e in self.registry("metadata_field_definitions.json") or []
        )
        if key in BOOLEANS:
            if value is not True:
                return False
            if key == "required" and prop.get("primaryKey") is True and settings.odcs.get("primaryKeyRequired") is not False:
                return True
            return True if key in keys else None
        if key == "primaryKeyPosition":
            return False if settings.odcs.get("primaryKeyPosition") is False else None
        if key == "partitionKeyPosition":
            return prop.get("partitioned") is True and "partitioned" in keys or None
        if key == "tags":
            names = {str(f.get("name")) for f in flags if f.get("systemKey") not in BOOLEANS}
            if settings.target("businessKey") == "tags":
                names.add(settings.property("businessKey"))
            return True if any(isinstance(t, str) and t in names for t in as_list(value)) else None
        if key == "customProperties":
            in_custom = lambda b: settings.target(b) == "customProperties"
            # Det Specly skriver i customProperties når filen sier det: forretningsnøkkelen, utviklernotatet, det nedstrøms
            # navnet (ikke når det er businessName, `columnBusinessNameSource: downstreamName`), de gamle nøklene og
            # kolonnefeltene.
            known = {settings.property(b) for b in ("businessKey", "developerNote") if in_custom(b)}
            if in_custom("downstreamName") and settings.odcs.get("columnBusinessNameSource") != "downstreamName":
                known.add(settings.property("downstreamName"))
            known |= {"legacyPrimaryKey", "legacyRequired", "legacyUnique"}
            for e in self.registry("metadata_field_definitions.json") or []:
                if "column" in entity_types(e) and isinstance(e.get("key"), str):
                    known |= {e["key"], e.get("odcsPropertyName") or e["key"], camel_case(e["key"])}
            # Det Specly skriver bare noen ganger: en kolonnestatus bare når den er en annen enn tabellens, kildene bare
            # når hver av dem finnes (som transformSourceObjects).
            maybe = {settings.property("columnStatus")} if in_custom("columnStatus") else set()
            entries = [e for e in as_list(value) if isinstance(e, dict)]
            lineage = settings.property("upstreamColumns") if in_custom("upstreamColumns") else None
            for e in entries:
                if lineage is not None and e.get("property") == lineage:
                    refs = as_list(e.get("value"))
                    resolved = refs and all(isinstance(r, str) and self.repo.resolve(r)[1] is not None for r in refs)
                    (known if resolved else maybe).add(lineage)
            if any(e.get("property") in known and e.get("value") not in (None, "", [], {}, False) for e in entries):
                return True
            if any(e.get("property") in maybe for e in entries):
                return None
            unwritten = {settings.property("downstreamName")} if in_custom("downstreamName") and settings.property("downstreamName") not in known else set()
            if as_list(settings.odcs.get("customProperties")) or any(isinstance(e.get("property"), str) and e["property"].endswith("Name") and e["property"] not in unwritten for e in entries):
                return None  # strukturerte egenskaper, eller et statusnavn: om Specly skriver dem, avgjør ikke sjekken
            return False if all(e.get("property") not in known for e in entries) else None
        if key == "quality":
            items = [i for i in as_list(value) if isinstance(i, dict)]
            ops = lambda i: any(op in i for op in OPERATORS)
            return True if any(i.get("type") == "text" or (i.get("type") == "library" and isinstance(i.get("metric"), str) and ops(i)) or (i.get("type") == "sql" and isinstance(i.get("query"), str) and ops(i)) for i in items) else None
        if key == "transformSourceObjects":
            refs = as_list(value)
            if settings.target("upstreamColumns") != "transformSourceObjects":
                return False
            return True if refs and all(isinstance(r, str) and self.repo.resolve(r)[1] is not None for r in refs) else None
        if key == "logicalTypeOptions":
            return True if isinstance(value, dict) and value else None
        if key in ("physicalName", "semanticType", "classification", "encryptedName", "transformLogic", "transformDescription", "synonyms", "examples", "enum"):
            return True if mapped(key) and specly_writes(value) else (False if not mapped(key) else None)
        if key == "relationships":
            return None
        return False

    def flag_rules(self):
        """Flaggreglene (`match_flag_rules`): hver aktive regel over hver kolonne; en kjøring legger bare til."""
        entries = self.registry("flag_rules.json")
        if not entries:
            return
        repo = self.repo
        file = repo.rel(repo.config_dir / "flag_rules.json")
        self.flag_entries = self.registry("flags.json")
        flags = self.flag_entries
        usable = []
        for index, rule in enumerate(entries):
            if rule.get("isActive") is False:
                continue
            mode, pattern, table_pattern = rule.get("matchMode"), rule.get("pattern"), rule.get("tableNamePattern")
            flag = None
            if flags is not None:
                flag = next((f for f in flags if isinstance(rule.get("flagUuid"), str) and str(f.get("uuid")).lower() == rule["flagUuid"].lower()), None)
                flag = flag or (next((f for f in flags if f.get("name") == rule.get("flag")), None) if rule.get("flagUuid") is None else None)
            label = rule.get("flag") or rule.get("flagUuid")
            why = None
            if rule.get("isActive") is not True:
                why = "isActive står ikke, og om Specly leser regelen som aktiv, avgjør ikke filene"
            elif flags is None:
                why = "flags.json mangler eller kan ikke leses, så flagget er ukjent"
            elif flag is None:
                why = f"flagget {label} står ikke i flags.json (finnes det bare i Specly, kjenner ikke sjekken det)"
            elif mode == "regex" and isinstance(pattern, str) and pattern.strip():
                why = rust_regex_unsafe(pattern)
            if not why and isinstance(table_pattern, str) and table_pattern:
                why = rust_regex_unsafe(table_pattern)
                why = why and f"tableNamePattern bruker {why}"
            elif why and mode == "regex":
                why = f"mønsteret bruker {why}" if not why.startswith(("isActive", "flags.json", "flagget")) else why
            if why:
                self.f.warning(file, 1, "rules.flag.undetermined", f"Flaggregelen /{index} ({label}, {mode} {pattern!r}): {why}. Hva den setter hvis reglene kjøres i Specly, avgjør ikke filene alene; sjekken gjetter ikke, og fix --apply-rules skriver det ikke.", self.rule_files("flag"))
                continue
            if not isinstance(pattern, str) or not pattern.strip() or mode not in MATCH_MODES:
                continue  # Et tomt mønster treffer ingenting (`expand_pattern`).
            expanded = pattern if mode == "regex" else ("^" if mode == "startsWith" else "") + re.escape(pattern) + ("$" if mode == "endsWith" else "")
            try:
                column_re = re.compile(expanded)
                table_re = re.compile(table_pattern) if isinstance(table_pattern, str) and table_pattern else None
            except re.error:
                continue  # Rust sin regex avviser også et mønster som ikke kan leses: regelen treffer ingenting.
            usable.append((index, flag, column_re, table_re, expanded, table_pattern if table_re else None))
        if not usable:
            return
        position = self.repo.settings.odcs.get("primaryKeyPosition") is False
        for table in repo.tables:
            if table.unreadable:
                continue
            for column in table.columns:
                if not column.name or not self.new_in_push(column):
                    continue
                have = self.column_flags(column)
                unknown = self.unknown_flags(column)
                added = []
                odd = None
                for index, flag, column_re, table_re, expanded, table_pattern in usable:
                    uuid = str(flag.get("uuid"))
                    if uuid in have or any(str(f.get("uuid")) == uuid for f in added):
                        continue
                    odd = regex_text_problem(expanded, column.name) or (table_pattern and regex_text_problem(table_pattern, table.name))
                    if odd:
                        odd = f"flaggregelen /{index} ({flag.get('name')}) og {odd}"
                        break
                    if column_re.search(column.name) and (table_re is None or table_re.search(table.name)):
                        added.append(flag)
                if odd:
                    self.rule_flags[id(column)] = {str(u[1].get("uuid")) for u in usable}
                    self.f.warning(table.file, column.line, "rules.flag.undetermined", f"{table.name}.{column.name}: {odd}. Hvilke flagg en kjøring av flaggreglene gir kolonnen, avgjør ikke filene alene; sjekken gjetter ikke, og fix --apply-rules skriver ingenting på kolonnen.", self.rule_files("flag"))
                    continue
                bound = [f for f in added if str(f.get("uuid")).lower() in self.bound_flags()]
                if bound:
                    names = ", ".join(str(f.get("name")) for f in bound)
                    self.rule_flags[id(column)] = {str(f.get("uuid")) for f in added}
                    self.f.warning(table.file, column.line, "rules.flag.undetermined", f"{table.name}.{column.name}: flaggreglene treffer kolonnen med {names}, som odcs.json binder til en customProperties-oppføring (eksporten skriver flagget der, ikke som tagg). Hvordan oppføringen da står, regner ikke sjekken ut, og om kolonnen har flagget fra før, kan ikke filene si sikkert; fix --apply-rules skriver ingenting på kolonnen.", self.rule_files("flag"))
                    continue
                if any(str(f.get("uuid")) in unknown for f in added):
                    # Påkrevd på en primærnøkkel med required: true: eksporten skriver den samme required: true med eller uten
                    # flagget, så filen endres ikke. Om Specly får flagget, avgjør ikke filene: flag_order på det er undetermined.
                    self.rule_flags[id(column)] = {str(f.get("uuid")) for f in added}
                    added = [f for f in added if str(f.get("uuid")) not in unknown]
                if not added:
                    continue
                self.rule_flags[id(column)] = self.rule_flags.get(id(column), set()) | {str(f.get("uuid")) for f in added}
                writes, why = self.flag_slots(column, added, position) if table.file not in self.multi_table_files() else (None, MULTI_TABLE)
                for flag in added:
                    item = self.f.warning(
                        table.file,
                        column.line,
                        "rules.flag.wouldAdd",
                        f"{table.name}.{column.name}: kjøres flaggreglene i Specly, får kolonnen flagget {flag.get('name')}, og neste eksport skriver det i kontrakten ({self.flag_text(flag)})." + ("" if writes is not None else f" fix --apply-rules skriver ikke dette: {why}."),
                        self.rule_files("flag"),
                    )
                    if writes is not None:
                        self.flag_writes.setdefault(repo.top / table.file, []).append((column, writes, item))
                        writes = []  # skrivingene for kolonnen står på det første funnet

    RULE_CONFIG = {
        "flag": ("flag_rules.json", "flags.json", "odcs.json"),
        "sort": ("column_sorting_rules.json", "flag_rules.json", "flags.json", "datatypes.json", "odcs.json"),
        "relation": ("relation_rules.json",),
    }

    def rule_files(self, kind, table=None):
        """Filene i config-mappen en regeltype leser: et funn nevner dem, så det vises med --changed-from når en av dem er
        endret slik at reglene kan gi noe annet (`config_changed`), eller, for sorteringen av `table`, når datatypes.json har
        fått eller mistet en datatype tabellens kolonner har (`types_touched`)."""
        names = [name for name in self.RULE_CONFIG[kind] if not self.baseline or self.config_changed(name) or (name == "datatypes.json" and table is not None and self.types_touched(table))]
        return [self.repo.rel(self.repo.config_dir / name) for name in names]

    def types_touched(self, table):
        """Om endringene i datatypes.json rører en datatype kolonnene i `table` har, og en datatype_group-regel finnes."""
        types = self.baseline.config_delta("datatypes.json") if self.baseline else None
        return types is not None and bool(self.rule_mentions("datatype")[0]) and types.names_any([c.prop.get(k) for c in table.columns for k in ("physicalType", "logicalType")])

    def config_changed(self, *names):
        """Om endringene i en av filene i config-mappen kan gi et annet utfall av reglene: da gjelder de overalt. En regelfil
        eller odcs.json: når JSON-en er en annen. flags.json: når en oppføring som er lagt til, tatt bort eller endret, er et
        flagg en flaggregel eller en flag_order-regel nevner. datatypes.json: når den er en datatype en datatype_group-regel
        nevner. En ny verdi ingen regel nevner, gir ingenting nytt i filer som ikke er endret."""
        b = self.baseline
        if b is None:
            return False
        for name in names:
            if name not in self.counted:
                delta = b.config_delta(name)
                kind = {"flags.json": "flag", "datatypes.json": "datatype"}.get(name)
                self.counted[name] = delta is not None and delta.changed and (kind is None or delta.names_any(*self.rule_mentions(kind)))
            if self.counted[name]:
                return True
        return False

    def rule_mentions(self, kind):
        """Navnene, uuid-ene og systemKey-ene på flaggene (`flag`) eller datatypene (`datatype`) reglene nevner."""
        if kind in self.mentions:
            return self.mentions[kind]
        names, uuids = [], []
        if kind == "flag":
            for rule in self.registry("flag_rules.json") or []:
                names.append(rule.get("flag"))
                uuids.append(rule.get("flagUuid"))
        for rule in self.registry("column_sorting_rules.json") or []:
            if kind == "flag" and rule.get("ruleType") == "flag_order":
                pattern = rule.get("pattern")
                uuids.extend(as_list(filter_list(pattern) if isinstance(pattern, str) else pattern))
            if kind == "datatype" and rule.get("ruleType") == "datatype_group":
                names.append(rule.get("dataType"))
                uuids.append(rule.get("datatypeUuid"))
        # Reglene når kolonnenes flagg og datatyper også gjennom navnet og systemKey (`column_flags`): en ny oppføring
        # med samme navn eller systemKey som en oppføring en regel nevner, gir også et annet utfall.
        keys = []
        delta = self.baseline.config_delta("flags.json" if kind == "flag" else "datatypes.json") if self.baseline else None
        wanted_uuids = {u.lower() for u in uuids if isinstance(u, str)}
        wanted_names = {n for n in names if isinstance(n, str)}
        for entry in (delta.old + delta.new) if delta is not None else []:
            if str(entry.get("uuid") or "").lower() in wanted_uuids or entry.get("name") in wanted_names:
                names.append(entry.get("name"))
                uuids.append(entry.get("uuid"))
                keys.append(entry.get("systemKey"))
        self.mentions[kind] = (names, uuids, keys)
        return self.mentions[kind]

    def enum_related(self, registry, value):
        """Registerfilen som `related` for et funn om verdien `value`: bare når endringene rører akkurat den verdien (tatt
        bort, nytt navn, eller lagt til med andre store og små bokstaver), så en ny verdi ikke viser hver kontrakt."""
        rel = self.repo.rel(self.repo.registry_path(registry))
        delta = self.baseline.config_delta(registry) if self.baseline else None
        return [rel] if delta is None or delta.names_any([str(value)]) else []

    def old_table(self, table):
        b = self.baseline
        return next((b.old_tables[k.lower()] for k in (table.id, table.name) if k and k.lower() in b.old_tables), None)

    def flag_fields(self, prop):
        """Det flaggreglene og flag_order leser på en kolonne, utenom navnet: taggene, konstruksjonsplassene og forretningsnøkkelen."""
        return [prop.get("tags")] + [prop.get(k) for k in BOOLEANS] + [self.repo.settings.value(prop, "businessKey")]

    def new_in_push(self, column):
        """Uten `--changed-from` hver kolonne; med, en kolonne der endringene rører noe flaggreglene leser: ny kolonne, nytt
        navn på kolonnen eller tabellen, taggene eller konstruksjonsplassene, eller flaggreglene, flaggene eller odcs.json."""
        if not self.baseline or self.config_changed(*self.RULE_CONFIG["flag"]):
            return True
        history = self.baseline.column_history(column)
        if not isinstance(history, dict):
            return history == "new"
        old = self.old_table(column.table)
        return str(history.get("name") or "") != column.name or (old is not None and old.name != column.table.name) or self.flag_fields(history) != self.flag_fields(column.prop)

    def order_in_push(self, table):
        """Uten `--changed-from` hver tabell; med, en tabell der endringene rører noe sorteringen leser: kolonnelisten,
        en kolonnes datatype eller flagg, tabellnavnet, excludeFromSorting, eller reglene og registrene den bruker."""
        b = self.baseline
        if not b or self.config_changed(*self.RULE_CONFIG["sort"]):
            return True
        if self.types_touched(table):
            return True  # en datatype kolonnene har, er lagt til eller tatt bort: datatype_group-regelen kan gi noe annet
        if table.file not in b.changed:
            return False
        old = self.old_table(table)
        if old is None or [c.name for c in old.columns] != [c.name for c in table.columns] or old.name != table.name:
            return True
        settings = self.repo.settings
        if settings.value(old.obj, "excludeFromSorting") != settings.value(table.obj, "excludeFromSorting"):
            return True
        read = lambda prop: (prop.get("physicalType"), prop.get("logicalType"), self.flag_fields(prop))
        return any(read(a.prop) != read(c.prop) for a, c in zip(old.columns, table.columns))

    def multi_table_files(self):
        """Kontraktene med mer enn én tabell i `schema`: der skriver fix ikke det reglene gir."""
        if getattr(self, "multi_files", None) is None:
            counts = {}
            for table in self.repo.tables:
                counts[table.file] = counts.get(table.file, 0) + 1
            self.multi_files = {f for f, n in counts.items() if n > 1}
        return self.multi_files

    def flag_text(self, flag):
        key = flag.get("systemKey")
        if key == "businessKey":
            return f"forretningsnøkkelen, der odcs.json sender businessKey"
        if key in BOOLEANS:
            return f"{key}: true" + (" og required: true" if key == "primaryKey" and self.repo.settings.odcs.get("primaryKeyRequired") is not False else "")
        return f"taggen {flag.get('name')}"

    def flag_slots(self, column, added, position):
        """Det eksporten skriver på kolonnen for de nye flaggene: `[(nøkkel, verdi)]`, eller `None` og hvorfor fix ikke skriver."""
        prop, writes = column.prop, []
        for flag in added:
            key = flag.get("systemKey")
            if key in ("businessKey", "partitioned"):
                return None, "plassen den skrives på (forretningsnøkkelen etter odcs.json, partitionKeyPosition) skriver ikke fix"
            if key == "primaryKey" and not position:
                return None, "primaryKeyPosition står ikke som false i odcs.json, så eksporten nummererer nøklene på nytt"
            if key in BOOLEANS:
                if key in prop:
                    return None, f"kolonnen har {key}: {json.dumps(prop.get(key))} fra før"
                writes.append((key, True))
                if key == "primaryKey" and self.repo.settings.odcs.get("primaryKeyRequired") is not False and prop.get("required") is not True and ("required", True) not in writes:
                    if "required" in prop:
                        return None, f"kolonnen har required: {json.dumps(prop.get('required'))} fra før"
                    writes.append(("required", True))
            else:
                tags = prop.get("tags")
                # En liste i flytstil skriver fix i blokkform først (format.differs), i samme kjøring.
                if tags is not None and not (isinstance(tags, Seq) and tags):
                    return None, "tags står ikke som en liste med tagger"
                if tags is not None and tags.flow and getattr(self, "format_ignored", False):
                    return None, "tags står i flytstil ([...]), og med --ignore format.differs skriver fix den ikke i blokkform først"
                if any(k == "tags" for k, _ in writes):
                    # Rekkefølgen mellom flere nye tagger er rekkefølgen Specly henter flaggreglene i (uten ORDER BY).
                    return None, "flere nye tagger på samme kolonne, og rekkefølgen Specly skriver dem i, står ikke i filene"
                writes.append(("tags", str(flag.get("name"))))
        # Hvor eksporten skriver en ny nøkkel: foran den neste av Speclys nøkler som filen har og Specly skriver.
        rendered = set()
        order = SHAPES["property"][0]
        for key, _ in writes:
            if key == "tags" and "tags" in prop:
                continue  # en ny tagg går sist i listen
            for later in order[order.index(key) + 1 :]:
                if later not in prop or any(k == later for k, _ in writes):
                    continue
                says = self.renders(column, later)
                if says is None:
                    return None, f"kolonnen har {later}, og om Specly skriver den (og den nye nøkkelen dermed står foran den eller sist i kolonnen), avgjør ikke filene"
                if says:
                    rendered.add(later)
                    break
        column.rendered = rendered | {later for later in order if later in prop and self.renders(column, later)}
        return writes, None

    def sorting_rules(self):
        """Kolonnesorteringsreglene (`decide_table_order`): reglene etter synkende priority, hver en stabil sortering."""
        entries = self.registry("column_sorting_rules.json")
        if not entries:
            return
        repo = self.repo
        file = repo.rel(repo.config_dir / "column_sorting_rules.json")
        active = [r for r in entries if r.get("isActive") is True]
        why = None
        if any(r.get("isActive") is None for r in entries):
            why = "en regel mangler isActive, og om Specly leser den som aktiv, avgjør ikke filene"
        elif any(not isinstance(r.get("priority"), int) or isinstance(r.get("priority"), bool) for r in active):
            why = "en aktiv regel har ikke et heltall i priority"
        else:
            priorities = [r["priority"] for r in active]
            same = sorted({p for p in priorities if priorities.count(p) > 1})
            if same:
                why = f"flere aktive regler har priority {', '.join(map(str, same))}, og rekkefølgen mellom dem er rekkefølgen de ble laget i Specly, som ikke står i filene"
        datatypes = {str(d.get("name")): str(d.get("uuid")) for d in self.registry("datatypes.json") or [] if d.get("uuid")}
        flag_uuids = {str(f.get("uuid")) for f in self.registry("flags.json") or []}
        rules = []
        for rule in sorted(active, key=lambda r: -r["priority"]) if not why else []:
            kind, pattern = rule.get("ruleType"), rule.get("pattern")
            label = rule.get("name") or kind
            if kind in ("pattern_first", "pattern_last") and isinstance(pattern, str) and pattern:
                problem = rust_regex_unsafe(pattern)
                if problem:
                    why = f"regelen {label} bruker {problem}"
                    break
                try:
                    rules.append((kind, re.compile(pattern, re.IGNORECASE), rule))
                except re.error:
                    why = f"regelen {label} har et mønster sjekken ikke kan lese"
                    break
            elif kind == "datatype_group":
                uuid = rule.get("datatypeUuid") if isinstance(rule.get("datatypeUuid"), str) and rule.get("datatypeUuid") else datatypes.get(rule.get("dataType"))
                if not uuid or uuid not in datatypes.values():
                    why = f"datatypen i regelen {label} står ikke i datatypes.json"
                    break
                rules.append((kind, uuid, rule))
            elif kind == "flag_order":
                order = filter_list(pattern) if isinstance(pattern, str) else pattern
                if not isinstance(order, list) or not order:
                    continue  # Uten flagg gjør regelen ingenting.
                if any(not isinstance(u, str) or u not in flag_uuids for u in order):
                    why = f"et flagg i regelen {label} står ikke i flags.json"
                    break
                rules.append((kind, order, rule))
            elif kind == "alphabetical":
                rules.append((kind, rule.get("direction") == "desc", rule))
        if why:
            self.f.warning(file, 1, "rules.sort.undetermined", f"Kolonnesorteringsreglene: {why}. Hvilken rekkefølge en kjøring i Specly gir kolonnene, avgjør ikke filene alene; sjekken gjetter ikke, og fix --apply-rules flytter ingen kolonner.", self.rule_files("sort"))
            return
        if not active:
            return  # Uten aktive regler sorterer en kjøring på navn; det melder ikke sjekken (se guiden).
        flags_by_name = {str(f.get("name")): str(f.get("uuid")) for f in self.registry("flags.json") or [] if f.get("uuid")}
        settings = repo.settings
        for table in repo.tables:
            if table.unreadable or len(table.columns) != len(table.properties) or not table.columns or any(not c.name for c in table.columns):
                continue
            if settings.value(table.obj, "excludeFromSorting") in (True, "true") or not self.order_in_push(table):
                continue
            columns = list(table.columns)
            reason = None
            for kind, arg, rule in rules:
                if kind == "alphabetical":
                    columns.sort(key=lambda c: nb_key(c.name), reverse=arg)
                elif kind in ("pattern_first", "pattern_last"):
                    # Sorteringsmønstrene skiller aldri store og små bokstaver (`decide_table_order`).
                    odd = next((p for p in (regex_text_problem(rule["pattern"], c.name, ignore_case=True) for c in columns) if p), None)
                    if odd:
                        reason = f"regelen {rule.get('name') or kind} og {odd}"
                    hit = [c for c in columns if arg.search(c.name)]
                    rest = [c for c in columns if not arg.search(c.name)]
                    columns = hit + rest if kind == "pattern_first" else rest + hit
                elif kind == "datatype_group":
                    types = {}
                    for c in columns:
                        # Datatypen innhentingen gir kolonnen: physicalType, ellers logicalType (`effective_type`).
                        name = next((c.prop.get(k) for k in ("physicalType", "logicalType") if isinstance(c.prop.get(k), str) and c.prop.get(k)), None)
                        if isinstance(name, str) and name and name not in datatypes:
                            reason = f"{table.name}.{c.name} har datatypen {name}, som ikke står i datatypes.json"
                        types[id(c)] = datatypes.get(name) if isinstance(name, str) else None
                    hit = [c for c in columns if types[id(c)] == arg]
                    columns = hit + [c for c in columns if types[id(c)] != arg]
                else:
                    if any(set(arg) & self.rule_flags.get(id(c), set()) for c in columns):
                        reason = f"flaggreglene ville gitt kolonner i {table.name} et flagg regelen {rule.get('name') or kind} sorterer på, og om de kjøres før eller etter, står ikke i filene"
                    unknown = next((c for c in columns if set(arg) & self.unknown_flags(c)), None)
                    if unknown is not None:
                        reason = f"regelen {rule.get('name') or kind} sorterer på flagget Påkrevd, og {table.name}.{unknown.name} er primærnøkkel med required: true: med primaryKeyRequired har den flagget bare hvis Specly allerede har gitt den det"
                    score = lambda c: min([arg.index(u) for u in self.column_flags(c) if u in arg] or [len(arg) + 1])
                    columns.sort(key=score)
            if reason:
                self.f.warning(table.file, table.line, "rules.sort.undetermined", f"{reason}. Hvilken rekkefølge en kjøring av kolonnesorteringsreglene gir {table.name}, avgjør ikke filene alene; fix --apply-rules flytter ingen kolonner.", self.rule_files("sort", table))
                continue
            if [c.index for c in columns] == [c.index for c in table.columns]:
                continue
            item = self.f.warning(
                table.file,
                table.line,
                "rules.sort.wouldReorder",
                f"Kjøres kolonnesorteringsreglene i Specly, får {table.name} kolonnene i rekkefølgen {', '.join(c.name for c in columns)}, og neste eksport flytter dem i filen. Sjekken regner fra rekkefølgen i filen (den Specly har når filen er det Specly holder).",
                self.rule_files("sort", table),
            )
            if table.file in self.multi_table_files():
                item["message"] += f" fix --apply-rules flytter ikke kolonnene: {MULTI_TABLE}."
                continue
            self.column_orders.setdefault(repo.top / table.file, []).append((table, [c.index for c in columns], item))

    def relation_rules(self):
        """Relasjonsreglene (`run_matcher`): bare et varsel, aldri fix. En ny relasjon får en tilfeldig id, og relasjoner som
        bare finnes i Specly stopper treff: sjekken kan ikke skrive den slik Specly ville."""
        entries = self.registry("relation_rules.json")
        if not entries:
            return
        repo = self.repo
        file = repo.rel(repo.config_dir / "relation_rules.json")
        # En endret relasjonsregelfil kan gi nye relasjoner overalt.
        changed = self.baseline.changed if self.baseline and not self.config_changed("relation_rules.json") else None
        tables = [t for t in repo.tables if not t.unreadable and not t.ghost and t.columns]
        existing = set()
        for table in tables:
            for column in table.columns:
                for rel in as_list(column.prop.get("relationships")):
                    targets = as_map(rel).get("to")
                    for target in targets if isinstance(targets, list) else [targets]:
                        other = repo.resolve(target)[1] if isinstance(target, str) else None
                        if other is not None:
                            existing.add((id(column), id(other)))
            for rel in as_list(table.obj.get("relationships")):
                ends = [as_map(rel).get(side) for side in ("from", "to")]
                if all(isinstance(e, str) for e in ends):
                    a, b = repo.resolve(ends[0])[1], repo.resolve(ends[1])[1]
                    if a is not None and b is not None:
                        existing.add((id(a), id(b)))
        rules = [r for r in entries if r.get("isActive") is True and isinstance(r.get("fromPattern"), str) and r["fromPattern"] and isinstance(r.get("toPattern"), str) and r["toPattern"]]
        rules.sort(key=lambda r: (r.get("order") if isinstance(r.get("order"), int) and not isinstance(r.get("order"), bool) else 0, str(r.get("uuid") or "")))
        names = [t.name for t in tables] + [c.name for t in tables for c in t.columns]
        # Kolonnene med hvert navn, for et mønster som etter plassholderne er ett helt navn (`^navn$`).
        index = {}
        for table in tables:
            for column in table.columns:
                index.setdefault(column.name, []).append(column)
        # Med --changed-from: bare par der minst én av tabellene er endret (`run_matcher` med tabellene som scope).
        in_scope = {id(t): changed is None or t.file in changed for t in tables}
        scoped = [t for t in tables if in_scope[id(t)]]
        # Kortnavnet hver tabell har i `{toTableShort}`/`{fromTableShort}`, fra tabelltypen i table_types.json.
        types = {str(e["name"]): e for e in self.registry("table_types.json") or [] if isinstance(e, dict) and e.get("name")}
        shorts = {}
        for table in tables:
            type_name = repo.settings.value(table.obj, "tableType")
            kind = types.get(type_name) or {} if isinstance(type_name, str) else {}
            shorts[id(table)] = short_name(table.name, kind.get("shortNameTemplate"), kind.get("delimiter"))
        for rule in rules:
            name = rule.get("name") or rule.get("uuid") or "uten navn"
            patterns = {k: normalize_pattern(rule[k]) if isinstance(rule.get(k), str) else ".*" for k in ("fromPattern", "toPattern", "fromTablePattern", "toTablePattern")}
            problem = next((p for p in (rust_regex_unsafe(placeholders(v, "x", "x")) for v in patterns.values()) if p), None)
            if not problem:
                # Med \w, \b, \s, \d, $ eller (?i) avgjør et tegn i et navn utenom ASCII og Latin-1-bokstavene ikke treffet.
                sensitive = [v for v in patterns.values() if CLASS_ESCAPE.search(v) or "$" in v or v.startswith("(?i)")]
                problem = next((p for v in sensitive for n in names for p in [regex_text_problem(v, n)] if p), None)
            if problem:
                self.f.warning(file, 1, "rules.relation.undetermined", f"Relasjonsregelen «{name}» bruker {problem}. Hvilke relasjoner den lager hvis reglene kjøres i Specly, avgjør ikke filene alene; sjekken gjetter ikke.", self.rule_files("relation"))
                continue
            found = self.relation_pairs(patterns, tables, scoped, in_scope, index, existing, shorts)
            if not found:
                continue
            shown = ", ".join(f"{a.table.name}.{a.name} → {b.table.name}.{b.name}" for a, b in found[:5])
            more = f" og {len(found) - 5} til (--json har dem ikke hver for seg; kjør regelen i Specly for hele listen)" if len(found) > 5 else ""
            scope = f" (blant tabellene endret siden {self.baseline_ref})" if changed is not None else ""
            self.f.warning(
                file,
                1,
                "rules.relation.wouldCreate",
                f"Relasjonsregelen «{name}» ville laget {len(found)} {'relasjon' if len(found) == 1 else 'relasjoner'}{scope} hvis reglene kjøres i Specly: {shown}{more}. Ingen av dem står i kontraktene. Relasjoner som bare finnes i Specly stopper et treff, og en ny relasjon får en id Specly lager, så fix skriver dem ikke.",
                sorted({c.table.file for pair in found for c in pair}) + self.rule_files("relation"),
            )

    def relation_pairs(self, patterns, tables, scoped, in_scope, index, existing, shorts):
        """Parene (fra-kolonne, til-kolonne) en relasjonsregel treffer, som `run_matcher`: hvert mønster lages én gang per
        tabell det avhenger av. Et kolonnemønster som etter plassholderne er ett helt navn, slås opp i stedet for å prøves
        mot hver kolonne. `shorts` har kortnavnet til hver tabell (etter `id`)."""
        compiled = {}

        def build(text):
            start, end = text.startswith("^"), text.endswith("$") and not text.endswith("\\$")
            body = text[1 if start else 0 : len(text) - (1 if end else 0)]
            if not REGEX_SPECIAL.search(body):
                return (start, end, body)
            try:
                return re.compile(text)
            except re.error:
                return None

        def pattern(text, cache=True):
            # Et mønster med plassholdere for begge tabellene blir ett per tabellpar: å huske dem alle ville holdt millioner
            # av mønstre i minnet på et stort repo, så det lages hver gang (re har sin egen cache for de siste).
            if not cache:
                return build(text)
            if text not in compiled:
                compiled[text] = build(text)
            return compiled[text]

        def hits(p, value):
            if p is None:
                return False
            if isinstance(p, tuple):
                start, end, body = p
                return value == body if start and end else value.startswith(body) if start else value.endswith(body) if end else body in value
            return p.search(value) is not None

        def exact(p):
            return p[2] if isinstance(p, tuple) and p[0] and p[1] else None

        used = {(key, side): any(f"{{{token}" in patterns[key] for token, _, s, _ in PLACEHOLDERS if s == side) for key in patterns for side in ("from", "to")}
        uses = lambda key, side: used[(key, side)]
        both = {key: used[(key, "from")] and used[(key, "to")] for key in patterns}
        # `a`/`b` er fra- og til-tabellen, eller None for en side mønsteret ikke fylles inn med.
        table_names = lambda t: ("", "") if t is None else (t.name, shorts[id(t)])
        fill = lambda key, a, b: placeholders(patterns[key], table_names(a)[0], table_names(b)[0], table_names(a)[1], table_names(b)[1])
        fixed = lambda key, a, b: pattern(fill(key, a, b), not both[key])
        to_table_ok, to_cols_ok = {}, {}

        def to_table_matched(source, target):
            if target is source or not target.columns:
                return False
            if uses("toTablePattern", "from"):
                return hits(fixed("toTablePattern", source, target), target.name)
            if id(target) not in to_table_ok:
                to_table_ok[id(target)] = hits(fixed("toTablePattern", None, target), target.name)
            return to_table_ok[id(target)]

        def to_columns(source, target):
            if uses("toPattern", "from"):
                p = fixed("toPattern", source, target)
                return [c for c in target.columns if hits(p, c.name)]
            if id(target) not in to_cols_ok:
                p = fixed("toPattern", None, target)
                to_cols_ok[id(target)] = [c for c in target.columns if hits(p, c.name)]
            return to_cols_ok[id(target)]

        found = []
        position = {id(t): n for n, t in enumerate(tables)}
        # Fra-kolonnemønsteret avhenger ikke av fra-tabellen, og til-sidens mønstre heller ikke: per til-tabell slås
        # kolonnenavnene mønsteret treffer opp blant fra-tabellenes kolonner (et mønster som er ren tekst, i én tekst
        # med alle navnene), i stedet for å prøve hvert par av tabeller.
        if not uses("fromPattern", "from") and not uses("toPattern", "from") and not uses("toTablePattern", "from"):
            by_name = {}
            for source in tables:
                if source.columns and hits(fixed("fromTablePattern", source, None), source.name):
                    for column in source.columns:
                        by_name.setdefault(column.name, []).append(column)
            names = NameIndex(by_name)
            for target in tables:
                if not to_table_matched(None, target):
                    continue
                to_cols = to_columns(None, target)
                if not to_cols:
                    continue
                for a in names.matching(fill("fromPattern", None, target), lambda text, value: hits(pattern(text), value)):
                    source = a.table
                    if source is target or not (in_scope[id(source)] or in_scope[id(target)]):
                        continue
                    found += [(a, b) for b in to_cols if (id(a), id(b)) not in existing and (id(b), id(a)) not in existing]
            return sorted(found, key=lambda p: (position[id(p[0].table)], position[id(p[1].table)], p[0].index, p[1].index))
        for source in tables:
            if not source.columns or not hits(fixed("fromTablePattern", source, None), source.name):
                continue
            from_fixed = None
            if not uses("fromPattern", "to"):
                p = fixed("fromPattern", source, None)
                from_fixed = [c for c in source.columns if hits(p, c.name)]
                if not from_fixed:
                    continue
            candidates = tables if in_scope[id(source)] else scoped
            # Til-mønsteret er ett helt navn som bare avhenger av fra-tabellen: tabellene med det navnet.
            name = exact(fixed("toPattern", source, None)) if not uses("toPattern", "to") else None
            if name is not None:
                seen = set()
                candidates = [c.table for c in index.get(name, []) if id(c.table) not in seen and not seen.add(id(c.table)) and (in_scope[id(source)] or in_scope[id(c.table)])]
            for target in candidates:
                if not to_table_matched(source, target):
                    continue
                if from_fixed is not None:
                    from_cols = from_fixed
                else:
                    p = fixed("fromPattern", source, target)
                    want = exact(p)
                    from_cols = [c for c in source.columns if c.name == want] if want is not None else [c for c in source.columns if hits(p, c.name)]
                if not from_cols:
                    continue
                to_cols = to_columns(source, target)
                for a in from_cols:
                    for b in to_cols:
                        if (id(a), id(b)) not in existing and (id(b), id(a)) not in existing:
                            found.append((a, b))
        return sorted(found, key=lambda p: (position[id(p[0].table)], position[id(p[1].table)], p[0].index, p[1].index))

    def auto_renames(self):
        """Et nytt navn eller nedstrømsnavn på en kolonne endrer navnet Specly gir kolonnene den er kilde til
        (`propagate_auto_translation_hook`, som også kjører på en innhenting): de som har det gamle navnet, kan bli omdøpt."""
        b = self.baseline
        if not b:
            return
        repo, settings = self.repo, self.repo.settings
        derive = lambda prop: (settings.downstream_name(prop) if isinstance(settings.downstream_name(prop), str) else "").strip() or str(prop.get("name") or "")
        cited = {}
        for table in repo.tables:
            if table.unreadable:
                continue
            for column in table.columns:
                for reference in self.sources_of(column):
                    parts = split_reference(reference)
                    if len(parts) >= 2:
                        cited.setdefault((parts[-2].lower(), parts[-1].lower()), []).append(column)
        for table in repo.tables:
            if table.unreadable or table.file not in b.changed:
                continue
            for column in table.columns:
                old = b.column_history(column)
                if not isinstance(old, dict):
                    continue
                before, after = derive(old), derive(column.prop)
                if before == after or not after:
                    continue
                old_name = str(old.get("name") or "")
                targets = []
                for key in {(table.name.lower(), column.name.lower()), (table.name.lower(), old_name.lower())}:
                    targets += [c for c in cited.get(key, []) if c not in targets and c is not column]
                # Specly omdøper bare en kolonne med én kilde (`enforce_single_source_rule`), og ikke en lenke med
                # nameDirection: toSource (der går navnet den andre veien).
                renamed = [c for c in targets if c.name == before and len(self.sources_of(c)) == 1 and not self.to_source(c)]
                if not renamed:
                    continue
                parts = []
                for target in renamed:
                    taken = any(c is not target and c.name == after for c in target.table.columns)
                    if taken:
                        parts.append(f"{target.table.name}.{target.name} (men {target.table.name} har allerede en kolonne {after}: da omdøper Specly den ikke, og slår av den automatiske oversettelsen)")
                        continue
                    downstream = sorted({c.table.file for c in cited.get((target.table.name.lower(), target.name.lower()), [])})
                    parts.append(f"{target.table.name}.{target.name} i {target.table.file}" + (f" (kildene til den står i {', '.join(downstream)})" if downstream else ""))
                self.f.warning(
                    table.file,
                    column.line,
                    "lineage.autoRename",
                    f"{table.name}.{column.name} fikk nytt navn eller nedstrømsnavn i endringene: navnet Specly avleder for kolonnene den er kilde til, går fra {before} til {after}. Kolonner som er automatisk oversatt fra den, omdøper Specly når endringen tas inn (det skjer også ved innhenting), og neste eksport skriver det nye navnet og de nye kildene (transformSourceObjects) i filene. Disse har det gamle navnet og kan bli omdøpt til {after}: {'; '.join(parts)}. Om en kolonne er automatisk oversatt (isAutoTranslated) står ikke i Git, så sjekken kan ikke si det sikkert; fix gjør ikke dette.",
                    sorted({t.table.file for t in renamed}),
                )

    def to_source(self, column):
        """Om kolonnens lenke står med nameDirection: toSource i filen."""
        return any(isinstance(e, dict) and e.get("nameDirection") == "toSource" for e in as_list(custom_properties(column.prop).get(self.repo.settings.property("upstreamColumns"))))

    def sources_of(self, column):
        """Kildene kolonnen nevner, som tekst (`lineage`, uten å melde noe)."""
        prop = column.prop
        out = []
        for entry in as_list(custom_properties(prop).get(self.repo.settings.property("upstreamColumns"))):
            if isinstance(entry, dict) and "sourceTable" in entry:
                out.append(f"{entry.get('sourceTable')}.{entry.get('sourceColumn')}")
            elif isinstance(entry, dict):
                out.append(entry.get("column"))
            else:
                out.append(entry)
        out = out or list(as_list(prop.get("transformSourceObjects")))
        return [r for r in out if isinstance(r, str)]

    def old_files(self, which, *keys):
        """Filene i `--changed-from` som ga et navn eller en id som nå mangler: da er funnet deres."""
        b = self.baseline
        return b.files_of(getattr(b, which), *keys) if b else []

    def data_products(self):
        """Dataproduktene slik Specly leser dem: formen, og at tabellene og diagrammene de nevner, finnes."""
        repo = self.repo
        table_ids = {t.id.lower() for t in repo.tables if t.id}
        table_names = [t.name for t in repo.tables]
        diagram_names = self.diagram_names
        by_id = {}
        for path, doc in repo.data_products:
            file = repo.rel(path)
            if path in repo.broken_yaml and doc is None:
                continue
            if not isinstance(doc, dict):
                self.f.error(file, 1, "odps.unreadable", ("Filen er tom (eller har bare kommentarer)." if doc is None else "Dataproduktet skal være nøkler med verdier (en YAML-mapping).") + " Specly kan ikke lese filen. Rett den, eller slett filen hvis dataproduktet skal bort.")
                continue
            problem = odps_problem(doc)
            if problem:
                self.f.error(file, problem[0], "odps.unreadable", problem[1])
                continue
            custom = as_list(doc.get("customProperties"))
            for index, entry in enumerate(custom):
                if not isinstance(entry, dict) or not isinstance(entry.get("value"), (list, str)):
                    continue
                line = line_of(custom, index)
                if entry.get("property") == "speclyId" and isinstance(entry["value"], str) and UUID.match(entry["value"]):
                    by_id.setdefault(entry["value"].lower(), []).append((file, line))
                if not isinstance(entry["value"], list):
                    continue
                for i, member in enumerate(entry["value"]):
                    at = line_of(entry["value"], i, line)
                    if entry.get("property") == "tables":
                        name, uuid = (member, "") if isinstance(member, str) else (member.get("name"), member.get("uuid") if isinstance(member.get("uuid"), str) else "")
                        if not (uuid and uuid.lower() in table_ids) and unique_name(table_names, name) is None:
                            self.f.error(file, at, "lint.dataProduct.danglingTable", f"Dataproduktet nevner tabellen {name}, som ikke finnes i Git (eller som flere tabeller heter). Specly tar den ikke med. Rett navnet eller fjern linjen.", self.old_files("old_table_files", name, uuid))
                    elif entry.get("property") == "diagrams" and isinstance(member, str) and unique_name(diagram_names, member) is None:
                        self.f.error(file, at, "lint.dataProduct.danglingDiagram", f"Dataproduktet nevner diagrammet {member}, som ikke finnes i Git (eller som flere diagrammer heter). Specly tar det ikke med. Rett navnet eller fjern linjen.", self.old_files("old_diagram_files", member))

        self.same_uuid(by_id, "Dataproduktet (speclyId)", "Slett den ene filen, eller ta bort speclyId i den nye (Specly lager en).")

    def diagrams(self):
        """Diagramfilene slik Specly leser dem: formen, plasseringene og at tabellene finnes."""
        repo = self.repo
        tables_by_id = {t.id.lower(): t for t in repo.tables if t.id and UUID.match(t.id)}
        table_names = [t.name for t in repo.tables]
        by_uuid = {}
        self.diagram_names = []
        for path, data in repo.diagrams:
            file = repo.rel(path)
            problem = diagram_problem(data)
            if problem:
                self.f.error(file, 1, "diagram.unreadable", problem)
                if isinstance(data, dict) and isinstance(data.get("name"), str):
                    self.diagram_names.append(data["name"])
                continue
            if not isinstance(data, dict) or not isinstance(data.get("uuid"), str) or not data["uuid"]:
                continue  # Ikke et diagram: Specly leser ingenting fra filen.
            self.diagram_names.append(data.get("name") or "")
            by_uuid.setdefault(data["uuid"].lower(), []).append((file, 1))
            seen = set()
            for index, item in enumerate(as_list(data.get("tables"))):
                hint = item.get("tableUuid") if isinstance(item.get("tableUuid"), str) else ""
                named = item.get("table") if isinstance(item.get("table"), str) else ""
                by_name = unique_name(table_names, named)
                if hint:
                    # Uten id i kontraktene (kort form) kjenner bare Specly tabellens uuid: da avgjør navnet.
                    stated = next((t for t in repo.by_name.get(named.lower(), []) if t.id and UUID.match(t.id)), None)
                    found = hint.lower() in tables_by_id or (stated is None and by_name is not None)
                    key = hint.lower()
                else:
                    found, key = by_name is not None, (by_name or "").lower()
                if not found:
                    self.f.error(file, 1, "lint.diagram.danglingTable", f"/tables/{index}: tabellen {named or hint} finnes ikke i Git. Specly tar den ikke med på diagrammet. Rett table og tableUuid, eller fjern plasseringen.", self.old_files("old_table_files", named, hint))
                    continue
                if key in seen:
                    continue
                seen.add(key)
                if not is_number(item.get("x")) or not is_number(item.get("y")):
                    self.f.error(file, 1, "diagram.unreadable", f"/tables/{index}: x og y skal være tall. Specly kan ikke lese filen før det er rettet.")
                    break

        self.diagram_names.extend(repo.unparsed_diagram_names)
        self.same_uuid(by_uuid, "Diagrammet", "Slett den ene filen, eller gi det nye diagrammet en ny uuid v4.")

    # ---------- Det eksportens patcher nekter (gitsync-formats patch.rs, odps_patch.rs) ----------
    #
    # En eksport skriver bare de endrede feltene inn i filens egen tekst. Noen former kan den ikke skrive
    # i: en eksport som må skrive en slik endring, stopper, uten å skrive filen på nytt (det gjør den bare
    # når filen ikke er gyldig YAML for den). Hver form stopper bare de endringene patcheren må skrive inn i
    # den (`tests/patch_refusals.rs`); andre endringer i filen går gjennom. Filen leses riktig inn.

    def refused(self, file, line, what, blocked, instead):
        self.f.error(file, line, "export.refused", f"{what} Specly leser filen, men en eksport som skal {blocked}, stopper på den. {instead}")

    def export_refusals(self):
        repo = self.repo
        contracts = {}
        for table in repo.tables:
            if not table.unreadable:
                contracts.setdefault(table.file, (table.contract, []))[1].append(table)
        for file, (contract, tables) in contracts.items():
            self.anchors(file)
            for key in ("id", "name", "dataProduct"):
                self.patched_key(file, contract, key, "Kontrakten")
            schema = contract.get("schema")
            self.list_form(file, schema, "schema", "en ny tabell")
            for table in tables:
                what = f"Tabellen {table.name}"
                if table.obj.flow:
                    self.refused(file, table.line, f"{what} står i flytstil ({{...}}).", f"skrive en endring i {table.name} sine felt (navn, beskrivelse, ...)", "Skriv den som en blokk: hver nøkkel på sin egen linje under `- `.")
                    continue
                for key in ("name", "description", "physicalType"):
                    self.patched_key(file, table.obj, key, what)
                self.list_form(file, table.obj.get("properties"), f"properties i {table.name}", "en ny kolonne")
                self.list_form(file, table.obj.get("quality"), f"quality i {table.name}", "en ny regel")
                self.flow_lists(file, table.obj, what)
                for column in table.columns:
                    where = f"Kolonnen {table.name}.{column.name}"
                    if column.prop.flow:
                        self.refused(file, column.line, f"{where} står i flytstil ({{...}}).", f"skrive en endring i {table.name}.{column.name} sine felt", "Skriv den som en blokk: hver nøkkel på sin egen linje under `- `.")
                        continue
                    for key in ("name", "description", "physicalType", "logicalType"):
                        self.patched_key(file, column.prop, key, where)
                    self.list_form(file, column.prop.get("quality"), f"quality i {table.name}.{column.name}", "en ny regel")
                    self.flow_lists(file, column.prop, where)
        for path, data in repo.data_products:
            if isinstance(data, dict):
                self.anchors(repo.rel(path))

    def anchors(self, file):
        """Et anker (`&navn`) eller en henvisning (`*navn`) hvor som helst i filen: patcheren nekter hele filen."""
        text = self.repo.texts.get(self.repo.top / file) or ""
        if not re.search(r"(?:^|[\s\[{,:])[&*][^\s\[\]{},]", text, re.M):
            return
        try:
            events = list(yaml.parse(text, Loader=Loader))
        except yaml.YAMLError:
            return
        for event in events:
            if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
                self.refused(file, event.start_mark.line + 1, "Filen bruker YAML-ankere (&navn) eller henvisninger til dem (*navn).", "skrive en endring hvor som helst i filen", "Skriv verdien ut på hvert sted (fix gjør det i en fil uten kommentarer).")
                return

    def patched_key(self, file, node, key, what):
        """`name`, `description`, `physicalType`, `logicalType` (og ved roten `id`, `name`, `dataProduct`) skriver patcheren
        rett inn i verdien: den må være én verdi, og noe må stå etter kolonet."""
        if not isinstance(node, Map) or key not in node:
            return
        if key in node.empty:
            self.refused(file, node.line_of(key), f"{what} har {key}: uten noe etter kolonet.", f"endre {key} der", f'Skriv {key}: "" eller {key}: null, eller ta bort linjen.')
        elif isinstance(node[key], (list, dict)):
            self.refused(file, node.line_of(key), f"{what} har {key} som er {kind_of(node[key])}, ikke én verdi.", f"endre {key} der", f"Skriv {key} som tekst.")

    def list_form(self, file, items, what, new):
        """En liste patcheren legger til i: i blokkform, med hvert element på samme linje som sin `-`."""
        if not isinstance(items, Seq) or not items:
            return
        if items.flow:
            self.refused(file, items.line, f"{what} står i flytstil ([...]).", f"legge til {new}", "Skriv listen som en blokk, ett element per `- `.")
            return
        # Patcheren ser bare på det første elementet: det nye får samme innrykk som det (patch.rs, `Edit::Append`).
        lines = (self.repo.texts.get(self.repo.top / file) or "").split("\n")
        first = items[0]
        if isinstance(first, Map) and not first.flow and 0 < first.line <= len(lines) and lines[first.line - 1][: first.column].strip() != "-":
            self.refused(file, line_of(items, 0), f"Det første elementet i {what} har `-` alene på linjen, og nøklene på linjene under.", f"legge til {new}", "Skriv den første nøkkelen på samme linje som `-` (- id: ...).")

    def flow_lists(self, file, node, what):
        """Kildene (`transformSourceObjects`, og en verdi i customProperties) tar patcheren ut én og én når en kilde
        slettes: en liste i flytstil over flere linjer kan den ikke det i."""
        lists = [("transformSourceObjects", node.get("transformSourceObjects"))]
        lists += [(f"customProperties ({e.get('property')})", e.get("value")) for e in as_list(node.get("customProperties")) if isinstance(e, dict)]
        for key, value in lists:
            if isinstance(value, Seq) and value.flow and value.multiline and value:
                self.refused(file, value.line, f"{what} har {key} som en liste i flytstil ([...]) over flere linjer.", "ta ut en kilde fordi kolonnen eller tabellen den peker på er slettet i Specly (den tas ut element for element)", "Skriv listen på én linje, eller som en blokk med ett element per `- `.")

    def files_outside_layout(self):
        """Filer av et slag Specly leser, men på et sted Specly ikke leser det slaget (`classify` i layout.rs)."""
        repo = self.repo
        known = set(REGISTRY_FILES + SETTING_FILES) - {"source_systems.json"}
        for folder, names, files in os.walk(repo.top):
            names[:] = sorted(n for n in names if not n.startswith(".") and n != "node_modules")
            folder = Path(folder)
            for name in sorted(files):
                path, file = folder / name, repo.rel(folder / name)
                if name.endswith(".odcs.yaml") and not inside(path, repo.tables_dir):
                    self.f.error(file, 1, "file.notRead", f"Specly leser kontrakter (.odcs.yaml) bare under {repo.rel(repo.tables_dir)}. Her leses ikke filen: en tabell som sto i den leses som slettet, en ny tabell blir ikke med. Flytt filen dit.")
                elif name.endswith(".odps.yaml") and not inside(path, repo.data_products_dir):
                    self.f.warning(file, 1, "file.notRead", f"Specly leser bare dataprodukter (.odps.yaml) i {repo.rel(repo.data_products_dir)}. Denne filen leses ikke. Flytt den dit.")
                elif not inside(path, repo.root):
                    continue
                elif name.endswith(".md") and folder != repo.concepts_dir and (inside(path, repo.concepts_dir) or self.is_concept(path)):
                    self.f.warning(file, 1, "file.notRead", f"Specly leser begreper (.md) bare direkte i {repo.rel(repo.concepts_dir)}, ikke i undermapper eller andre mapper. Denne filen leses ikke. Flytt den dit.")
                elif name in known and folder != repo.config_dir:
                    self.f.warning(file, 1, "file.notRead", f"Specly leser {name} bare direkte i {repo.rel(repo.config_dir)}. Denne filen leses ikke. Flytt den dit.")
                elif name.endswith(".json") and not inside(path, repo.diagrams_dir) and not inside(path, repo.config_dir) and self.is_diagram(path):
                    self.f.warning(file, 1, "file.notRead", f"Specly leser diagrammer bare under {repo.rel(repo.diagrams_dir)}. Denne filen leses ikke. Flytt den dit.")

    def is_concept(self, path):
        try:
            head = path.read_bytes()[:4096].decode("utf-8", "replace").lstrip("\ufeff")
        except OSError:
            return False
        return head.startswith("---") and re.search(r"^uuid:", head, re.M) is not None

    def is_diagram(self, path):
        try:
            if path.stat().st_size > 5_000_000:
                return False
            data = json.loads(path.read_bytes().decode("utf-8-sig"))
        except (OSError, ValueError):
            return False
        return isinstance(data, dict) and isinstance(data.get("uuid"), str) and isinstance(data.get("tables"), list)

    def files_not_read(self):
        """Filer som ser ut som kontrakter eller dataprodukter, men som Specly ikke leser."""
        repo = self.repo
        self.files_outside_layout()
        tables, products = repo.tables_dir, repo.data_products_dir
        skip = lambda path, base: any(part.startswith(".") for part in path.relative_to(base).parts)
        seen = set()
        for base in (repo.root, tables):
            if not base.is_dir():
                continue
            for pattern in ("*.yml", "*.yaml"):
                for path in sorted(base.rglob(pattern)):
                    if path in seen or skip(path, base) or path.name.endswith(".odcs.yaml"):
                        continue
                    seen.add(path)
                    name, file = path.name, repo.rel(path)
                    in_products = inside(path, products)
                    if name.endswith(".odps.yaml"):
                        continue
                    if name.endswith((".odcs.yml", ".odps.yml")):
                        self.f.warning(file, 1, "file.notRead", f"Specly leser bare filer som slutter på .odcs.yaml og .odps.yaml. Denne filen leses ikke. Gi den endelsen {name[:-4]}.yaml.")
                    elif inside(path, tables) and not in_products and not inside(path, repo.config_dir):
                        # En annen YAML-fil i tabellmappen meldes bare når den sier at den er en kontrakt.
                        try:
                            head = path.read_bytes()[:4096].decode("utf-8", "replace")
                        except OSError:
                            continue
                        if re.search(r"^kind:\s*[\"']?Data(Contract|Product)\b", head, re.M):
                            self.f.warning(file, 1, "file.notRead", "Filen sier at den er en kontrakt (kind), men Specly leser bare filer som slutter på .odcs.yaml og .odps.yaml. Denne filen leses ikke. Gi den riktig endelse.")

    def ambiguous_plain(self):
        """Ukvoterte verdier Specly leser som tekst og en YAML 1.1-leser (PyYAML og mange verktøy) som noe annet: `Yes`
        er teksten Yes for Specly og True for PyYAML, så samme fil er to ulike data (pilot 19.11). Lest av teksten i
        filen (`quote_yaml11`), ikke av hva PyYAML gjør av den."""
        repo = self.repo
        registry = repo.source_systems_path if repo.source_systems_path.suffix == ".yaml" else None
        paths = ([registry] if registry else []) + repo.contract_paths + repo.concept_paths + [p for p, _ in repo.data_products]
        for path in paths:
            text = repo.read_text(path) if path.is_file() else None
            if text is None or path in repo.broken_yaml:
                continue
            text = text[1:] if text.startswith("﻿") else text
            front, first = frontmatter(text)[:2] if path.suffix == ".md" else (text, 0)
            try:
                node = yaml.compose(front, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
            except yaml.YAMLError:
                continue
            lines = text.split("\n")
            spots = [n for n in yaml11_plain_values(node, set()) if lines[n.start_mark.line + first][n.start_mark.column : n.end_mark.column] == n.value]
            if not spots:
                continue
            # Anførselstegnet eksporten setter: i registeret filens eget (`yaml_registry_text` i config.rs), ellers
            # det Specly skriver kontrakter, dataprodukter og begreper med (`to_yaml`).
            quote_all = repo.settings.quote_all
            if path == registry:
                quotes = value_quotes(node)
                quote = "'" if quotes["'"] and not quotes['"'] and not quote_all else '"'
                when = "Specly gjør det selv ved neste eksport av filen, i hver oppføring"
            else:
                quote = '"' if quote_all else "'"
                when = "En eksport setter anførselstegn rundt en slik verdi den skriver, ikke rundt en den ikke endrer"
            file, out = repo.rel(path), []
            for n in spots:
                line = n.start_mark.line + first
                quoted = json.dumps(n.value, ensure_ascii=False) if quote == '"' else f"'{n.value}'"
                item = self.f.error(file, line + 1, "yaml.ambiguousPlain", f"`{n.value}` står uten anførselstegn. Specly leser det som teksten {n.value}, men en YAML 1.1-leser (PyYAML og mange andre verktøy) leser det som {yaml11_reading(n.value)}: samme fil gir to ulike data. Sett anførselstegn rundt verdien: {quoted}. {when}; fix gjør det nå.")
                out.append((line, n.start_mark.column, n.end_mark.column, quoted, item))
            self.ambiguous[path] = out

    def format(self):
        repo = self.repo
        for path, kind in repo.format_files():
            file = repo.rel(path)
            if not path.is_file() or (self.baseline and file not in self.baseline.changed):
                continue
            text = repo.read_text(path)
            if text is None or path in repo.broken_yaml:
                continue  # Meldt som en fil som ikke kan leses. `fix` rører den ikke: da ville innhold forsvunnet.
            try:
                wanted = formatted(text, kind, repo.settings.quote_all)
            except (yaml.YAMLError, ValueError):
                continue  # Meldt som en fil som ikke kan leses.
            if wanted is None or wanted == text:
                continue
            self.reformatted[path] = (text, wanted, kind)
            line, expected = first_difference(text, wanted)
            report = self.f.error if self.strict else self.f.warning
            if kind == "registry":
                when = "En eksport skriver bare oppføringene som er endret i Specly, i Specly-format; resten av filen står som den står."
            elif path.parent == repo.config_dir and path.name in REGISTRY_FILES:
                when = "Neste eksport som tar en endring i dette registeret, skriver hele filen i Specly-format."
            else:
                when = "En eksport endrer bare felt som er endret i Specly, i filens egen form og rekkefølge (en form den ikke kan skrive i, meldes som export.refused), og skriver ikke om filen for formatets skyld."
            report(file, line, "format.differs", f"Linje {line} er ikke slik Specly skriver filen. Specly skriver: {expected}. Innholdet leses riktig. {when} fix skriver linjen slik, uten å endre innholdet eller rekkefølgen.")


def inside(path, base):
    """`path` ligger i mappen `base` (på et hvilket som helst nivå). Som `base in path.parents`, uten å bygge listen."""
    return str(path).startswith(str(base) + os.sep)


def unique_name(names, name):
    """Det ene navnet i `names` som er `name`: nøyaktig, ellers uten hensyn til store og små bokstaver."""
    if not isinstance(name, str):
        return None
    exact = [n for n in names if n == name]
    if len(exact) != 1:
        exact = exact or [n for n in names if n.lower() == name.lower()]
    return exact[0] if len(exact) == 1 else None


def loose(name):
    return name.strip().lower()


class Names(set):
    """Navnene i et register uten mellomrom først og sist og med små bokstaver; `exact` har dem slik de er skrevet.
    Specly kjenner en verdi bare slik den er skrevet: et navn med andre store og små bokstaver, eller med et mellomrom
    først eller sist, er ikke det samme navnet for Specly (refs.rs `unknown_name`/`unknown_type`)."""

    def __init__(self, names):
        names = list(names)
        super().__init__(loose(n) for n in names)
        self.exact = set(names)
        self.spelled = {}
        for n in names:
            self.spelled.setdefault(loose(n), n)

    def problem(self, value):
        """`None` når Specly kjenner verdien, `case` når bare store og små bokstaver eller mellomrom først og sist skiller
        den fra et navn i registeret (sannsynligvis en skrivefeil), ellers `unknown`."""
        if value in self.exact:
            return None
        return "case" if loose(value) in self else "unknown"

    def like(self, value):
        """Navnet i registeret `value` sannsynligvis skulle vært, i anførselstegn så et mellomrom synes."""
        return json.dumps(self.spelled.get(loose(value), ""), ensure_ascii=False)


def link_kind(entry):
    """`(link, source, exceptions)` for en lenke i en begrepsfil, med Speclys navn i filen."""
    if not isinstance(entry, dict):
        return "linked", "manual", []
    names = {"linked_with_exceptions": "linkedWithExceptions", "rule_based": "ruleBased"}
    kind = names.get(entry.get("link"), entry.get("link") or "linked")
    source = names.get(entry.get("source"), entry.get("source") or "manual")
    # Unntakene gjelder bare en lenke med unntak.
    exceptions = as_list(entry.get("exceptions")) if kind == "linkedWithExceptions" else []
    return kind, source, exceptions


def own_texts(settings, column):
    """Kolonnens egne tekster slik Specly leser dem inn (beskrivelse, utviklernotat, nedstrømsnavn)."""
    text = lambda v: v if isinstance(v, str) else ""
    return {
        "businessDescription": text(column.prop.get("description")),
        "developerNote": text(settings.value(column.prop, "developerNote")),
        "downstreamName": text(settings.downstream_name(column.prop)),
    }


def column_data_type(column):
    """Datatypen Specly leser for kolonnen: physicalType, ellers logicalType."""
    for key in ("physicalType", "logicalType"):
        value = column.prop.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def link_path(column):
    escape = lambda s: s.replace(".", "\\.")
    return f"{escape(column.table.name)}.{escape(column.name)}"


def flow_entry(entry):
    """En lenke på én linje, til en melding."""
    value = lambda v: "[" + ", ".join(v) + "]" if isinstance(v, list) else json.dumps(v, ensure_ascii=False) if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", v) else v
    return "{" + ", ".join(f"{k}: {value(v)}" for k, v in entry.items()) + "}"


def camel_case(key):
    """Navnet Specly gir et felt uten eget ODCS-navn (`default_property_name`)."""
    if "_" not in key:
        return key
    parts = [p for p in key.split("_") if p]
    return (parts[0].lower() if parts else "") + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def text_slot(settings, field):
    """Nøkkelen på kolonnen en arvet tekst skrives i, når den er en egen nøkkel (ikke customProperties)."""
    if field == "businessDescription":
        return "description"
    if field == "downstreamName" and settings.odcs.get("columnBusinessNameSource") == "downstreamName":
        return "businessName"
    target = settings.target(field)
    return target if target and target not in ("customProperties", "tags") else None


def status_names(entries):
    """Navnene en status kan ha i en kontrakt: navnet, og ODCS-verdien den er koblet til."""
    if entries is None:
        return None
    return Names(str(e.get(key)) for e in entries for key in ("name", "odcsStatus") if e.get(key))


class RuleMatcher:
    """Hvilket begrep reglene lenker en kolonne til, slik Specly regner det ut (`match_rules`).

    Reglene prøves i rekkefølgen begrepets uuid, regelens `order`, plassen i
    filen. Den første som treffer, vinner. En kolonne som er `excluded` fra et
    begrep, hoppes over bare av det begrepets regler. Et filter sjekken ikke kan
    regne ut fra filene (dataprodukt, metadata, kolonnefelt), gir ikke noe svar
    for kolonnen: da sies hvorfor.
    """

    def __init__(self, repo, concepts):
        self.repo = repo
        self.rules = []
        self.invalid = []
        for concept in sorted(concepts, key=lambda c: c.uuid):
            rules = [r for r in as_list(concept.data.get("rules")) if isinstance(r, dict) and r.get("isActive") is not False and isinstance(r.get("columnNamePattern"), str)]
            for rule in sorted(rules, key=lambda r: r.get("order") if isinstance(r.get("order"), int) else 0):
                patterns = [rule.get("columnNamePattern") if rule.get("isRegex") else None, rule.get("tableNamePattern")]
                why = next((w for w in map(rust_regex_problem, patterns) if w), None)
                if why:
                    self.invalid.append((concept, rule, why))
                    continue  # Specly kan ikke lese mønsteret: regelen treffer ingenting.
                self.rules.append((concept, rule, self.pattern(patterns[0]), self.pattern(patterns[1])))
        self.by_value = {}
        self.uuids = {name: self.by_name(name) for name in ("table_types.json", "table_statuses.json", "datatypes.json")}

    @staticmethod
    def pattern(text):
        if not isinstance(text, str) or not text:
            return None
        try:
            return re.compile(text)
        except re.error:
            return False  # Et ugyldig mønster treffer ingenting.

    def by_name(self, registry):
        out = {}
        for entry in self.repo.registry(registry) or []:
            for key in ("name", "odcsStatus"):
                if entry.get(key) and entry.get("uuid"):
                    out.setdefault(str(entry[key]), str(entry["uuid"]))
        return out

    def candidates(self, field, value):
        """Reglene som treffer på navnet, i den rekkefølgen de prøves."""
        key = (field, value)
        if key not in self.by_value:
            found = []
            for index, (_, rule, name_pattern, _) in enumerate(self.rules):
                if (rule.get("matchField") == "downstreamName") != (field == "downstreamName"):
                    continue
                if rule.get("isRegex"):
                    if name_pattern and name_pattern.search(value):
                        found.append(index)
                elif value == rule.get("columnNamePattern"):
                    found.append(index)
            self.by_value[key] = found
        return self.by_value[key]

    def concept(self, column, downstream_name, excluded=()):
        """`(begrep, regel, None)` for regelen som vinner, `(None, None, None)` når ingen treffer, `(None, None, hvorfor)` når filene ikke avgjør det."""
        table = column.table
        settings = self.repo.settings
        for index in sorted(self.candidates("columnName", column.name) + self.candidates("downstreamName", downstream_name)):
            concept, rule, _, table_pattern = self.rules[index]
            if rule.get("tableNamePattern"):
                if not table_pattern or not table_pattern.search(table.name):
                    continue
            if any(filter_list(rule.get(key)) for key in ("dataProductFilter", "metadataFilter", "columnFieldFilter")):
                return None, None, f"en regel i {concept.name} har et filter på dataprodukt, metadata eller kolonnefelt, som sjekken ikke kan regne ut fra filene"
            verdict = True
            root_status = settings.target("tableStatus") == "status"
            for key, registry, name in (
                ("tableTypeFilter", "table_types.json", settings.value(table.obj, "tableType")),
                ("tableStatusFilter", "table_statuses.json", settings.value(table.contract if root_status else table.obj, "tableStatus")),
                ("columnTypeFilter", "datatypes.json", column_data_type(column)),
            ):
                allowed = filter_list(rule.get(key))
                if not allowed:
                    continue
                uuid = self.uuids[registry].get(name) if isinstance(name, str) else None
                if name and uuid is None:
                    return None, None, f"en regel i {concept.name} filtrerer på {key}, og {name} står ikke i {registry} med uuid"
                if uuid not in allowed:
                    verdict = False
            if verdict and concept.uuid not in excluded:
                return concept, rule, None
        return None, None, None


# Det Rust sin regex (som Specly matcher reglene med) ikke kan, men Python sin `re` kan, eller leser annerledes.
RUST_REGEX_UNSUPPORTED = (
    (re.compile(r"\(\?<?[=!]"), "lookahead/lookbehind ((?=, (?!, (?<=, (?<!)"),
    (re.compile(r"\\[1-9]|\(\?P=|\\k<|\\g<"), "en tilbakereferanse"),
    (re.compile(r"\(\?>"), "en atomisk gruppe ((?>)"),
    (re.compile(r"(?<!\\)[*+?}]\+"), "en possessiv kvantor (*+, ++, ?+)"),
    (re.compile(r"\\Z"), "\\Z (Rust kjenner bare \\z)"),
    (re.compile(r"\(\?\(|\(\?[aLu]"), "et Python-særtrekk ((?(…), (?a), (?L), (?u))"),
)


def rust_regex_problem(pattern):
    """Hvorfor Specly (Rust sin regex) ikke kan lese mønsteret, eller `None`. Begge leser `\\d` og `\\w` som Unicode,
    skiller store og små bokstaver og søker i teksten (ikke hel match), så resten matcher likt."""
    if not isinstance(pattern, str) or not pattern:
        return None
    for check, what in RUST_REGEX_UNSUPPORTED:
        if check.search(pattern):
            return what
    return None


# Det sjekken regner som likt i Rust sin regex og Python sin `re` for reglene i config-mappen: tegn,
# `\d \w \s \b` og deres store bokstaver, skjulte tegn (`\.`), `.`, `^`, `$`, `|`, grupper `(` og `(?:`,
# tegnklasser uten nøstede klasser eller mengdeoperasjoner, kvantorene `* + ?` (også late) og
# `{m}`, `{m,}`, `{m,n}`, og `(?i)` først. Alt annet kan bety noe annet (eller ingenting) i Rust.
SAFE_ESCAPES = set("dDwWsSbB") | set(".^$|?*+()[]{}\\/-")


def rust_regex_unsafe(pattern):
    """Hvorfor sjekken ikke kan si at mønsteret treffer det samme i Specly (Rust sin regex) som i Python, eller `None`."""
    if not isinstance(pattern, str) or not pattern:
        return None
    problem = rust_regex_problem(pattern)
    if problem:
        return problem
    if len(pattern) > MAX_PATTERN:
        return f"et mønster på over {MAX_PATTERN} tegn, som Rust kan avvise som for stort"
    i, n = (4, len(pattern)) if pattern.startswith("(?i)") else (0, len(pattern))
    after_atom, counted = False, 0
    while i < n:
        c = pattern[i]
        if c == "\\":
            if i + 1 >= n or pattern[i + 1] not in SAFE_ESCAPES:
                return f"\\{pattern[i + 1 : i + 2]}, som Rust og Python kan lese ulikt"
            i, after_atom = i + 2, True
        elif c == "[":
            j = i + 1
            if j < n and pattern[j] == "^":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                if pattern[j] == "[" or pattern[j : j + 2] in ("&&", "--", "~~"):
                    return "en nøstet tegnklasse eller mengdeoperasjon i [...]"
                if pattern[j] == "\\":
                    # [\b] er backspace i Python, men en feil i Rust.
                    if j + 1 >= n or pattern[j + 1] not in SAFE_ESCAPES or pattern[j + 1] in "bB":
                        return f"\\{pattern[j + 1 : j + 2]} i [...]"
                    j += 1
                j += 1
            if j >= n:
                return "en tegnklasse som ikke lukkes"
            i, after_atom = j + 1, True
        elif c == "(":
            if pattern[i + 1 : i + 2] == "?" and pattern[i + 1 : i + 3] != "?:":
                return "en gruppe med (? som ikke er (?:"
            i, after_atom = i + (3 if pattern[i + 1 : i + 3] == "?:" else 1), False
        elif c in "*+?":
            if not after_atom:
                return "en kvantor uten noe foran"
            i += 2 if pattern[i + 1 : i + 2] == "?" else 1
            after_atom = False
        elif c == "{":
            m = re.match(r"\{([0-9]+)(,([0-9]*))?\}\??", pattern[i:])
            if not m or not after_atom:
                return "{ som ikke er en gyldig gjentakelse ({m}, {m,} eller {m,n})"
            # Rust sin regex har en grense for hvor stort et mønster blir (10 MB kompilert; \w{250} er over): over den kan
            # det ikke leses, og regelen treffer ingenting, mens Python treffer. Sjekken godtar tall som til sammen er
            # høyst MAX_REPEAT, og ingen talt gjentakelse av en gruppe.
            counted += max(int(m.group(1)), int(m.group(3) or 0))
            if counted > MAX_REPEAT or pattern[i - 1] == ")":
                return f"gjentakelsen {m.group(0)} (tallene til sammen over {MAX_REPEAT}, eller på en gruppe), som Rust kan avvise som for stor"
            i, after_atom = i + len(m.group(0)), False
        elif c in ")|^$":
            i, after_atom = i + 1, c == ")"
        elif c == "}" or c == "]":
            return f"et {c} uten noe som åpner det"
        else:
            i, after_atom = i + 1, True
    return None


MAX_REPEAT = 100
MAX_PATTERN = 200
MULTI_TABLE = "kontrakten har flere tabeller i schema, og hvordan eksporten skriver det reglene gir i en slik fil, avgjør ikke sjekken"
# Tegnene Rust og Python er enige om med \w \W \b \B \s \S \d \D, $ og uten forskjell på store og små bokstaver: synlige
# ASCII-tegn og bokstavene i Latin-1 (æ, ø, å, é ...), uten ß og ÿ (som ikke har en enkel stor bokstav i Latin-1).
# Ellers skiller de seg: ² er \w i Python, ikke i Rust; en kombinerende ring (å skrevet a + U+030A) er \w i Rust, ikke
# i Python; \x1c er \s i Python; ı, İ, ſ og K (kelvin) brettes ulikt.
NAME_SAFE = frozenset(chr(c) for c in range(0x20, 0x7F)) | (frozenset(chr(c) for c in range(0xC0, 0x100)) - frozenset("×÷ßÿ"))
CLASS_ESCAPE = re.compile(r"(?<!\\)(?:\\\\)*\\[wWbBsSdD]")


def regex_text_problem(pattern, text, ignore_case=False):
    """Hvorfor sjekken ikke kan si at `pattern` treffer `text` likt i Rust og Python, eller `None`."""
    ignore_case = ignore_case or pattern.startswith("(?i)")
    if "\n" in text and "$" in pattern:
        return f"et linjeskift i {text!r}, og $ treffer foran et linjeskift på slutten i Python, ikke i Rust"
    if not (ignore_case or CLASS_ESCAPE.search(pattern)):
        return None
    odd = sorted({c for c in text + (pattern if ignore_case else "") if c not in NAME_SAFE})
    if not odd:
        return None
    shown = ", ".join(repr(c) if c.isprintable() else f"U+{ord(c):04X}" for c in odd[:3])
    return f"tegnet {shown} i {text!r}" + (" eller mønsteret" if ignore_case else "") + ", som Rust og Python kan lese ulikt med \\w, \\b, \\s, \\d, $ eller uten forskjell på store og små bokstaver"


def nb_key(name):
    """Sorteringsnøkkelen Specly sorterer kolonnenavn på (`nb_sort_key`): små bokstaver, tegn og sifre før a-z, så æ, ø, å."""
    out = []
    for c in name:
        lower = c.lower()[:1] or c
        o = ord(lower)
        if "0" <= lower <= "9":
            out.append(500 + o - 48)
        elif "a" <= lower <= "z":
            out.append(1000 + o - 97)
        elif lower in "æøå":
            out.append(1026 + "æøå".index(lower))
        elif o < 128:
            out.append(o)
        else:
            out.append(2000 + o)
    return out


def normalize_pattern(pattern):
    """En `*` uten `.` foran leses som `.*` (`normalize_pattern`)."""
    return "".join(".*" if c == "*" and (i == 0 or pattern[i - 1] != ".") else c for i, c in enumerate(pattern))


# (plassholder, store bokstaver, side, kortnavn), i rekkefølgen `replace_placeholders` bytter dem.
PLACEHOLDERS = (
    ("fromTableShort", False, "from", True),
    ("FROM_TABLE_SHORT", True, "from", True),
    ("toTableShort", False, "to", True),
    ("TO_TABLE_SHORT", True, "to", True),
    ("tableName", False, "from", False),
    ("TABLE_NAME", True, "from", False),
    ("fromTable", False, "from", False),
    ("FROM_TABLE", True, "from", False),
    ("toTable", False, "to", False),
    ("TO_TABLE", True, "to", False),
)


REGEX_SPECIAL = re.compile(r"[\\.+*?()|\[\]{}^$#&\-~]")
PLACEHOLDER_FORM = re.compile(r"\\?\{(" + "|".join(token for token, _, _, _ in PLACEHOLDERS) + r")\\?\}")
PLACEHOLDER_TOKENS = {token: (upper, side, short) for token, upper, side, short in PLACEHOLDERS}
TEMPLATES = {}
TABLE_NAME_PART = re.compile(r"\{table_name_part:(-?[0-9]+)\}")
TABLE_NAME_PARTS = re.compile(r"\{table_name_parts:(-?[0-9]+):(-?[0-9]+)\}")


def table_name_template(template, table_name, delimiter):
    """Malen med `{table_name}`, `{table_name_part:n}` og `{table_name_parts:a:b}` fylt inn fra tabellnavnet, delt på
    skilletegnet (`substitute_table_name_placeholders`). Et negativt tall teller bakfra; en del utenfor navnet er tom."""
    parts = table_name.split(delimiter)
    index = lambda digits: len(parts) + int(digits) if int(digits) < 0 else int(digits)
    s = template.replace("{table_name}", table_name)
    s = TABLE_NAME_PART.sub(lambda m: parts[index(m.group(1))] if 0 <= index(m.group(1)) < len(parts) else "", s)
    return TABLE_NAME_PARTS.sub(lambda m: delimiter.join(p for i, p in enumerate(parts) if index(m.group(1)) <= i <= index(m.group(2))), s)


def short_name(table_name, template, delimiter):
    """Kortnavnet `{toTableShort}`/`{fromTableShort}` står for (`matcher::short_name`): tabelltypens kortnavnmal brukt
    på tabellnavnet, med typens skilletegn (`__` uten). Hele navnet når tabellen ikke har type, typen ikke har mal, eller
    malen gir tom tekst."""
    template = template.strip() if isinstance(template, str) else ""
    if not template:
        return table_name
    delimiter = delimiter if isinstance(delimiter, str) and delimiter else "__"
    return table_name_template(template, table_name, delimiter) or table_name


def placeholders(pattern, from_table, to_table, from_short=None, to_short=None):
    """Plassholderne i et relasjonsmønster byttet med tabellnavnene og kortnavnene (hele navnet når kortnavnet ikke er
    gitt), som tekst (ikke escapet) (`replace_placeholders`)."""
    if "{" not in pattern:
        return pattern
    from_short = from_table if from_short is None else from_short
    to_short = to_table if to_short is None else to_short
    if not any("{" in name for name in (from_table, to_table, from_short, to_short)):
        # Mønsteret delt opp én gang (en relasjonsregel fylles inn for hvert tabellpar); det samme som å bytte én
        # plassholder om gangen når ingen av navnene selv har en plassholder i seg.
        parts = TEMPLATES.get(pattern)
        if parts is None:
            parts, at = [], 0
            for m in PLACEHOLDER_FORM.finditer(pattern):
                parts += [pattern[at : m.start()], PLACEHOLDER_TOKENS[m.group(1)]]
                at = m.end()
            parts.append(pattern[at:])
            TEMPLATES[pattern] = parts
        values = None
        if len(parts) > 1:
            names = {("from", False): from_table, ("to", False): to_table, ("from", True): from_short, ("to", True): to_short}
            values = {(upper, side, short): name.upper() if upper else name for (side, short), name in names.items() for upper in (False, True)}
        return "".join([p if p.__class__ is str else values[p] for p in parts])
    for token, upper, side, short in PLACEHOLDERS:
        value = (from_short if short else from_table) if side == "from" else (to_short if short else to_table)
        value = value.upper() if upper else value
        for form in ("\\{" + token + "\\}", "\\{" + token + "}", "{" + token + "\\}", "{" + token + "}"):
            pattern = pattern.replace(form, value)
    return pattern


class NameIndex:
    """Kolonnenavnene et mønster treffer. Et mønster som er ren tekst (eventuelt med `^` og `$`, slik de fleste blir
    når plassholderne er byttet ut) slås opp i én tekst med alle navnene i stedet for å prøves mot hvert navn."""

    def __init__(self, by_name):
        self.by_name = by_name
        self.joined = "\n" + "\n".join(by_name) + "\n"

    def matching(self, pattern, search):
        start, end = pattern.startswith("^"), pattern.endswith("$") and not pattern.endswith("\\$")
        body = pattern[1 if start else 0 : len(pattern) - (1 if end else 0)]
        if any(c in body for c in ".^$|?*+()[]{}\\"):
            return [c for name, cs in self.by_name.items() if search(pattern, name) for c in cs]
        if start and end:
            return list(self.by_name.get(body, []))
        needle = ("\n" if start else "") + body + ("\n" if end else "")
        out, seen, at = [], set(), self.joined.find(needle)
        while at >= 0:
            first = self.joined.rfind("\n", 0, at + (1 if start else 0)) + 1
            name = self.joined[first : self.joined.find("\n", at + (1 if start else 0) + len(body))]
            if name not in seen:
                seen.add(name)
                out.extend(self.by_name.get(name, []))
            at = self.joined.find(needle, at + 1)
        return out


def filter_list(value):
    """Et regelfilter som liste eller mapping: skrevet slik, eller som JSON i en tekst."""
    if isinstance(value, str) and value.strip():
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, (list, dict)) else []


# ---------- Formatet Specly skriver ----------
#
# Specly skriver YAML med libyaml (ingen linjebryting, tekst med linjeskift
# som `|`-blokk), setter anførselstegn rundt tekst etter innstillingen
# `quoteAllStrings`, og rykker hver liste inn to tegn under nøkkelen. JSON
# skrives med to tegns innrykk. Funksjonene under gjør det samme, i samme
# rekkefølge, så en fil Specly har skrevet, kommer ut tegn for tegn lik.


class Plain(str):
    """En verdi som ikke er tekst (tall, true, false, null), slik Specly skriver den."""


INT = re.compile(r"^[+-]?[0-9]+$")
RADIX = re.compile(r"^([+-]?)0(x[0-9a-fA-F]+|o[0-7]+|b[01]+)$")
FLOAT = re.compile(r"^[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?$")
INFINITY = {".inf": ".inf", ".Inf": ".inf", ".INF": ".inf", "+.inf": ".inf", "+.Inf": ".inf", "+.INF": ".inf", "-.inf": "-.inf", "-.Inf": "-.inf", "-.INF": "-.inf", ".nan": ".nan", ".NaN": ".nan", ".NAN": ".nan"}
OPERATORS = ["mustBe", "mustNotBe", "mustBeGreaterThan", "mustBeGreaterOrEqualTo", "mustBeLessThan", "mustBeLessOrEqualTo", "mustBeBetween", "mustNotBeBetween"]
# Rekkefølgen Specly skriver nøklene i, og hva som ligger under hver nøkkel.
# En nøkkel som ikke står her, blir stående der den er.
SHAPES = {
    "contract": (
        ["apiVersion", "kind", "version", "id", "name", "tenant", "status", "servers", "dataProduct", "domain", "schema", "contractCreatedTs", "slaProperties", "support", "team", "customProperties"],
        {"schema": "object", "servers": "server", "customProperties": "custom"},
    ),
    "object": (
        ["id", "name", "physicalType", "logicalType", "properties", "description", "businessName", "tags", "physicalName", "dataGranularityDescription", "deprecated", "synonyms", "context", "customProperties", "relationships", "quality"],
        {"properties": "property", "customProperties": "custom", "relationships": "relationship", "quality": "quality"},
    ),
    "property": (
        ["id", "name", "physicalType", "logicalType", "description", "businessName", "primaryKey", "primaryKeyPosition", "required", "unique", "partitioned", "partitionKeyPosition", "criticalDataElement", "deprecated"]
        + ["physicalName", "semanticType", "classification", "encryptedName", "transformLogic", "transformDescription", "synonyms", "examples", "enum", "tags"]
        + ["relationships", "logicalTypeOptions", "transformSourceObjects", "customProperties", "quality"],
        {"customProperties": "custom", "relationships": "relationship", "quality": "quality"},
    ),
    "quality": (["id", "type", "name", "description", "metric", "arguments"] + OPERATORS + ["dimension", "severity", "engine", "implementation", "scheduler", "schedule", "query"], {}),
    "relationship": (["id", "type", "from", "to", "customProperties"], {"customProperties": "custom"}),
    "custom": (["id", "property", "value"], {}),
    "server": (["server", "type", "catalog", "schema"], {}),
    "odps": (
        ["apiVersion", "kind", "id", "name", "version", "status", "description", "domain", "tags", "support", "type", "tenant", "productCreatedTs", "team", "outputPorts", "customProperties"],
        {"team": "team", "outputPorts": "port", "customProperties": "custom"},
    ),
    "team": (["name", "members"], {}),
    "port": (["name", "description"], {}),
    # Nøklene øverst i en begrepsfil skrives alfabetisk, lenkene etter sti og reglene etter `order`.
    "concept": ([], {"columns": "link", "rules": "rule"}),
    "link": (["exceptions", "link", "path", "source", "columnUuid"], {}),
    "rule": (
        ["columnNamePattern", "matchField", "isRegex", "tableNamePattern", "tableTypeFilterNames", "tableTypeFilter", "dataProductFilterNames", "dataProductFilter"]
        + ["tableStatusFilterNames", "tableStatusFilter", "columnTypeFilterNames", "columnTypeFilter", "metadataFilter", "columnFieldFilter", "isActive", "order"],
        {},
    ),
}


def digits_but_not_number(text):
    text = text[1:] if text[:1] in ("+", "-") else text
    return len(text) > 1 and text[0] == "0" and all("0" <= c <= "9" for c in text[1:])


def plain_scalar(text):
    """En ukvotert verdi slik Specly leser den: `Plain` for null, bool og tall, ellers teksten selv."""
    if text in ("", "null", "Null", "NULL", "~"):
        return Plain("null")
    if text in ("true", "True", "TRUE"):
        return Plain("true")
    if text in ("false", "False", "FALSE"):
        return Plain("false")
    radix = RADIX.match(text)
    if radix:
        return Plain(str(int(radix.group(1) + radix.group(2)[1:], {"x": 16, "o": 8, "b": 2}[radix.group(2)[0]])))
    if digits_but_not_number(text):
        return text
    if INT.match(text) and -(2**127) <= int(text) < 2**128:
        return Plain(str(int(text)))
    if text in INFINITY:
        return Plain(INFINITY[text])
    if FLOAT.match(text):
        number = float(text)
        if number not in (float("inf"), float("-inf")):
            return Plain(float_text(number))
    return text


def float_text(number):
    """Et desimaltall slik Rust skriver det (korteste form som gir samme tall)."""
    text = repr(number)
    sign, text = ("-", text[1:]) if text.startswith("-") else ("", text)
    mantissa, _, exponent = text.partition("e")
    whole, _, fraction = mantissa.partition(".")
    digits, point = whole + fraction, len(whole) + int(exponent or 0)
    stripped = digits.lstrip("0")
    point -= len(digits) - len(stripped)
    digits = stripped.rstrip("0")
    if not digits:
        return sign + "0.0"
    if len(digits) <= point <= 16:
        return sign + digits + "0" * (point - len(digits)) + ".0"
    if 0 < point <= 16:
        return sign + digits[:point] + "." + digits[point:]
    if -5 < point <= 0:
        return sign + "0." + "0" * -point + digits
    return sign + digits[0] + ("." + digits[1:] if len(digits) > 1 else "") + "e" + str(point - 1)


class KeyClash(Exception):
    """To nøkler i samme mapping blir samme tekst (1 og "1"), eller en nøkkel er ikke en enkel verdi: formatet kan ikke
    skrives uten å miste innhold, så filen skrives ikke om."""


def specly_value(node):
    """Innholdet i en YAML-node slik Specly holder det, i filens egen rekkefølge: rekkefølgen på nøkler, lister og
    tagger er aldri formatets (en eksport lar en fil som er lik som verdier stå, og beholder ellers Gits rekkefølge;
    kolonne- og regelrekkefølge som er data, dømmer reglene, ikke formatsjekken)."""
    if isinstance(node, yaml.MappingNode):
        out = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, yaml.ScalarNode) or key_node.value in out:
                raise KeyClash()
            out[key_node.value] = specly_value(value_node)
        return out
    if isinstance(node, yaml.SequenceNode):
        return [specly_value(child) for child in node.value]
    return plain_scalar(node.value) if not node.style else node.value


def yaml_events(value):
    if isinstance(value, dict):
        yield yaml.MappingStartEvent(None, None, True, flow_style=False)
        for key, item in value.items():
            yield from yaml_events(key)
            yield from yaml_events(item)
        yield yaml.MappingEndEvent()
    elif isinstance(value, list):
        yield yaml.SequenceStartEvent(None, None, True, flow_style=False)
        for item in value:
            yield from yaml_events(item)
        yield yaml.SequenceEndEvent()
    elif isinstance(value, Plain):
        yield yaml.ScalarEvent(None, None, (True, True), str(value))
    else:
        # Tekst med linjeskift skrives som blokk. Tekst som ellers ville blitt lest
        # som noe annet enn tekst, får enkle anførselstegn. Resten avgjør libyaml.
        style = "|" if "\n" in value else "'" if isinstance(plain_scalar(value), Plain) or digits_but_not_number(value) else None
        yield yaml.ScalarEvent(None, None, (True, True), value, style=style)


EMITTER = getattr(yaml, "CDumper", yaml.Dumper)
SEPARATORS = (("\u2028", "\u0001\ue000", "\\x01\ue000", "\\L"), ("\u2029", "\u0002\ue000", "\\x02\ue000", "\\P"))


def stand_in(value):
    """Linjeskilletegnene U+2028 og U+2029 byttet med noe libyaml bare kan skrive i doble anførselstegn."""
    if isinstance(value, dict):
        return {stand_in(key): stand_in(item) for key, item in value.items()}
    if isinstance(value, list):
        return [stand_in(item) for item in value]
    if isinstance(value, Plain):
        return value
    for separator, stand, _, _ in SEPARATORS:
        value = value.replace(separator, stand)
    return value


def render_yaml(value, quote_all):
    events = [yaml.StreamStartEvent(), yaml.DocumentStartEvent(explicit=False), *yaml_events(stand_in(value)), yaml.DocumentEndEvent(explicit=False), yaml.StreamEndEvent()]
    text = yaml.emit(events, Dumper=EMITTER, width=1 << 30, allow_unicode=True)
    for _, _, emitted, escape in SEPARATORS:
        text = text.replace(emitted, escape)
    return indent_sequences(rewrite_values(text, double_quote if quote_all else quote_yaml11))


def double_quote(value):
    """En tekst i doble anførselstegn. Tall, true, false, null og `[]`/`{}` står som de er."""
    if value.startswith("'"):
        value = value[1:-1].replace("''", "'")
    elif value[:1] in ("[", "{") or isinstance(plain_scalar(value), Plain):
        return None
    return json.dumps(value, ensure_ascii=False)


YAML11_WORDS = {"y", "yes", "n", "no", "true", "false", "on", "off", "null", "~", "<<", "=", ".inf", "+.inf", "-.inf", ".nan"}


def quote_yaml11(value):
    """En tekst en YAML 1.1-leser (PyYAML) ville lest som noe annet: `Yes`, `on`, `0123`, `12:30`, `2026-11-19`.
    Samme regel som Specly skriver med (`yaml11_not_a_string` i odcs.rs)."""
    if value.startswith("'") or isinstance(plain_scalar(value), Plain):
        return None
    other = value.lower() in YAML11_WORDS or sexagesimal(value) or yaml11_number(value) or yaml11_timestamp(value)
    return f"'{value}'" if other else None


def yaml11_reading(value):
    """Hva en YAML 1.1-leser gjør av en verdi `quote_yaml11` setter anførselstegn rundt."""
    lower = value.lower()
    if lower in ("null", "~"):
        return "null (ingen verdi)"
    if lower in ("y", "yes", "n", "no", "true", "false", "on", "off"):
        return "en sannhetsverdi (true/false)"
    if yaml11_timestamp(value):
        return "en dato"
    return "noe annet enn tekst" if lower in ("<<", "=") else "et tall"


def yaml11_plain_values(node, seen):
    """Verdiene (ikke nøklene) i `node`, ukvotert på én linje, som Specly leser som tekst og en YAML 1.1-leser som noe
    annet (`quote_yaml11`)."""
    if node is None or id(node) in seen:
        return
    seen.add(id(node))
    if isinstance(node, yaml.MappingNode):
        for _, value in node.value:
            yield from yaml11_plain_values(value, seen)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            yield from yaml11_plain_values(item, seen)
    elif not node.style and node.start_mark.line == node.end_mark.line and quote_yaml11(node.value):
        yield node


def value_quotes(node, seen=None):
    """Hvor mange verdier i `node` som står i `"`, i `'`, og som tekst uten anførselstegn (`string_quotes` i odcs.rs:
    en verdi `quote_yaml11` setter anførselstegn rundt, telles ikke, den får filens)."""
    seen = set() if seen is None else seen
    out = {'"': 0, "'": 0, None: 0}
    if node is None or id(node) in seen:
        return out
    seen.add(id(node))
    children = [v for _, v in node.value] if isinstance(node, yaml.MappingNode) else node.value if isinstance(node, yaml.SequenceNode) else None
    if children is None:
        if node.style in ('"', "'"):
            out[node.style] += 1
        elif not node.style and not isinstance(plain_scalar(node.value), Plain) and not quote_yaml11(node.value):
            out[None] += 1
        return out
    for child in children:
        for key, count in value_quotes(child, seen).items():
            out[key] += count
    return out


def sexagesimal(value):
    text = value[1:] if value[:1] in ("+", "-") else value
    text, _, fraction = text.partition(".")
    head, *groups = text.split(":")
    digit = lambda c: "0" <= c <= "9"
    return (
        bool(groups)
        and digit(head[:1])
        and all(digit(c) or c == "_" for c in head)
        and all((len(g) == 1 and digit(g)) or (len(g) == 2 and "0" <= g[0] <= "5" and digit(g[1])) for g in groups)
        and all(digit(c) or c == "_" for c in fraction)
    )


def yaml11_number(value):
    text = (value[1:] if value[:1] in ("+", "-") else value).replace("_", "")
    digit = lambda c: "0" <= c <= "9"
    for prefix, allowed in (("0x", "0123456789abcdefABCDEF"), ("0X", "0123456789abcdefABCDEF"), ("0b", "01"), ("0o", "01234567")):
        if text.startswith(prefix):
            return len(text) > 2 and all(c in allowed for c in text[2:])
    if not (digit(text[:1]) or text[:1] == ".") or not any(digit(c) for c in text) or not all(digit(c) or c in ".eE+-" for c in text):
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def yaml11_timestamp(value):
    parts = value.split("-", 2)
    if len(parts) < 3:
        return False
    year, month, rest = parts
    digit = lambda c: "0" <= c <= "9"
    day = 0
    while day < len(rest) and digit(rest[day]):
        day += 1
    if not (len(year) == 4 and all(map(digit, year)) and 1 <= len(month) <= 2 and all(map(digit, month)) and 1 <= day <= 2):
        return False
    if day == len(rest):
        return True
    return rest[day] in "Tt \t" and digit(rest[day + 1 :].lstrip()[:1])


def split_value(rest):
    """En linje uten listemerker delt i nøkkel og verdi."""
    end = None
    if rest[:1] in ("'", '"'):
        quote, i = rest[0], 1
        while i < len(rest):
            if rest[i] == "'" and quote == "'" and rest[i + 1 : i + 2] == "'":
                i += 2
            elif rest[i] == "\\" and quote == '"':
                i += 2
            elif rest[i] == quote:
                end = i + 1
                break
            else:
                i += 1
    else:
        end = rest.find(": ")
        if end < 0:
            end = len(rest) - 1 if rest.endswith(":") else None
    if end is not None and rest[end:].startswith(": "):
        return rest[:end], rest[end + 2 :]
    if end is not None and rest[end:] == ":":
        return rest[:end], None
    return None, rest


def strip_markers(body, indent):
    rest = body[indent:]
    while rest.startswith("- "):
        rest = rest[2:]
    return rest


def rewrite_values(text, rewrite):
    """libyaml sin tekst med hver verdi `rewrite` gir en ny form for, byttet ut."""
    out, block_indent = [], None
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\n")
        indent = len(body) - len(body.lstrip())
        if block_indent is not None:
            if not body.strip() or indent > block_indent:
                out.append(line)
                continue
            block_indent = None
        rest = strip_markers(body, indent)
        key, value = split_value(rest)
        # En kommentar, eller en linje som verken er `key: ` eller `- ` (en tekst som fortsetter fra linjen over).
        if value is None or rest.startswith("#") or (key is None and len(rest) == len(body) - indent):
            out.append(line)
            continue
        if value.startswith("|"):
            block_indent = indent
        replaced = rewrite(value) if value[:1] not in ('"', "|") else None
        out.append(line if replaced is None else body[: len(body) - len(value)] + replaced + line[len(body) :])
    return "".join(out)


def indent_sequences(text):
    """Hver liste rykket inn to tegn under nøkkelen sin."""
    out, opened, key_column, block_indent = [], [], None, None
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\n")
        indent = len(body) - len(body.lstrip())
        if not (block_indent is not None and (not body.strip() or indent > block_indent)):
            block_indent = None
            item = body[indent:].startswith("- ")
            while opened and (opened[-1] > indent or (opened[-1] == indent and not item)):
                opened.pop()
            if item and key_column == indent:
                opened.append(indent)
            rest = strip_markers(body, indent)
            key, value = split_value(rest)
            key_column = len(body) - len(rest) if key is not None and value is None else None
            if value is not None and value.startswith("|"):
                block_indent = indent
        out.append(("  " * len(opened) if body else "") + line)
    return "".join(out)


def js_numbers(value):
    """Et heltall skrevet som desimaltall (`100.0`) skrives som heltall, som i JavaScript."""
    if isinstance(value, dict):
        return {key: js_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [js_numbers(item) for item in value]
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e21:
        return int(value)
    return value


def formatted(text, kind, quote_all):
    """`text` slik Specly ville skrevet det samme innholdet, eller `None` for en tom fil."""
    # Specly skriver ikke BOM, og bare `\n` som linjeskift.
    text = text[1:] if text.startswith("\ufeff") else text
    if kind == "json":
        return json.dumps(js_numbers(json.loads(text)), indent=2, ensure_ascii=False)
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    if kind == "registry":
        # Eksporten skriver bare oppføringene som endres (`yaml_registry_text` i config.rs), med hver tekst i `"` når
        # prosjektet har quoteAllStrings eller filen har hver tekst i `"`: formatet her er bare de anførselstegnene.
        quotes = value_quotes(yaml.compose(text, Loader=loader))
        if not (quote_all or (quotes['"'] and not quotes["'"] and not quotes[None])):
            return text
        return rewrite_values(text, lambda v: None if " #" in v or v[:1] in (">", "&", "*", "!") else double_quote(v))
    if kind == "concept":
        text = text.replace("\r\n", "\n")
    if kind != "concept":
        node = yaml.compose(text, Loader=loader)
        try:
            return None if node is None else render_yaml(specly_value(node), quote_all)
        except KeyClash:
            return None
    lines = text.split("\n")
    close = next((i for i, line in enumerate(lines[1:], start=1) if line.rstrip() == "---"), None)
    if lines[0].rstrip() != "---" or close is None:
        return None
    front = "\n".join(lines[1:close]) + "\n"
    node = yaml.compose(front, Loader=loader)
    if node is None:
        return None
    try:
        rendered = own_keys_as_written(front, node, render_yaml(specly_value(node), quote_all))
    except KeyClash:
        return None
    return "---\n" + rendered + "---\n" + "\n".join(lines[close + 1 :])


def own_keys_as_written(front, node, rendered):
    """`rendered` med nøklene Specly ikke skriver i en begrepsfil (`owner: team`) slik de står i `front`: dem leser
    Specly ikke, og eksporten lar dem stå (#3024), så formatet deres er ikke formatsjekkens sak."""
    if not isinstance(node, yaml.MappingNode) or node.flow_style or all(k.value in CONCEPT_KEYS for k, _ in node.value):
        return rendered

    def blocks(text, mapping):
        lines = text.split("\n")
        starts = [k.start_mark.line for k, _ in mapping.value] + [len(lines) - 1]
        return [(k.value, "\n".join(lines[starts[i] : starts[i + 1]]).rstrip("\n")) for i, (k, _) in enumerate(mapping.value)]

    ours = blocks(rendered, yaml.compose(rendered, Loader=yaml.SafeLoader))
    theirs = dict(blocks(front, node))
    return "\n".join(theirs[key] if key not in CONCEPT_KEYS else block for key, block in ours) + "\n"


def first_difference(text, wanted):
    """Den første linjen som er ulik, og hva Specly skriver der."""
    have, want = text.split("\n"), wanted.split("\n")
    for index in range(max(len(have), len(want))):
        ours = have[index] if index < len(have) else None
        theirs = want[index] if index < len(want) else None
        if ours != theirs:
            if theirs is None or (theirs == "" and index == len(want) - 1 and ours is not None):
                return min(index + 1, len(have)), "ingen flere linjer (filen slutter her)"
            shown = theirs.strip()
            return min(index + 1, len(have)), "`" + (shown[:77] + "..." if len(shown) > 80 else shown) + "`" if shown else "en tom linje"
    return 1, "det samme"


def has_comments(text, kind):
    """Om en YAML-fil har kommentarer. `fix` skriver ikke en slik fil på nytt: da ville de forsvunnet."""
    if kind == "json":
        return False
    if kind == "concept":
        text = frontmatter(text)[0]
    end = 0
    try:
        for token in yaml.scan(text, Loader=yaml.SafeLoader):
            if "#" in text[end : token.start_mark.index]:
                return True
            end = token.end_mark.index
    except yaml.YAMLError:
        return True
    return "#" in text[end:]


# ---------- Det eksporten skriver inn i en fil som står i Git ----------
#
# Eksporten skriver ikke filen på nytt: den legger det som er nytt inn i Git sin
# tekst (gitsync-formats/src/patch.rs), og resten står som det står. Funksjonene
# under gjør det samme, linje for linje, for det fix legger til: en ny lenke i
# en begrepsfil, et nytt felt på en kolonne og en uuid på et begrep.


def plain_ok(value):
    """Om en tekst kan stå uten anførselstegn (`plain_ok`)."""
    return (
        bool(value)
        and not value[0].isspace()
        and not value[-1].isspace()
        and value[0] not in "-?:,[]{}#&*!|>'\"%@`"
        and not any(escaped_char(c) for c in value)
        and ": " not in value
        and " #" not in value
        and not value.endswith(":")
        and not isinstance(plain_scalar(value), Plain)
        and not digits_but_not_number(value)
    )


def escaped_char(c):
    return (ord(c) < 32 or 127 <= ord(c) < 160) or c in "\ufeff\u2028\u2029\ufffe\uffff"


def rust_double_quoted(value):
    out = []
    for c in value:
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif escaped_char(c):
            out.append(f"\\u{ord(c):04X}")
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


def style_of(text):
    return {'"': "double", "'": "single", "|": "literal", ">": "folded"}.get(text[:1], "plain")


def dominant_style(text):
    """Anførselstegnene de fleste tekstverdiene bruker; uten anførselstegn ved likt (`dominant_style`)."""
    count = {"plain": 0, "single": 0, "double": 0}
    for line in text.split("\n"):
        rest = line.strip()
        while rest.startswith("- "):
            rest = rest[2:].lstrip()
        if ": " not in rest:
            continue
        key, value = rest.split(": ", 1)
        if not key or not all(c.isalnum() or c in "-_." for c in key):
            continue
        value = value.lstrip()
        first = value[:1]
        if first == '"':
            count["double"] += 1
        elif first == "'":
            count["single"] += 1
        elif first and first not in "|>[{#&*":
            try:
                parsed = yaml.safe_load(value)
            except yaml.YAMLError:
                continue
            if isinstance(parsed, str) and not isinstance(plain_scalar(value), Plain):
                count["plain"] += 1
    best = "plain"
    if count["single"] > count[best]:
        best = "single"
    if count["double"] > count[best]:
        best = "double"
    return best


def render_scalar(value, style, dominant, indent):
    """`(første linje, blokklinjer)` for en tekst i stilen til feltet den skrives i (`render`)."""
    if isinstance(value, bool):
        return ("true" if value else "false"), []
    if isinstance(value, list):
        return "", [indent + "- " + render_scalar(item, "plain", dominant, "")[0] for item in value]
    if "\n" in value or style in ("literal", "folded"):
        text = value.rstrip("\n")
        trailing = len(value) - len(text)
        ok = bool(text) and text[0] not in " \t" and not any(c == "\r" or (escaped_char(c) and c not in "\n\t") for c in value)
        if not ok:
            return rust_double_quoted(value), []
        folded = style == "folded" and "\n" not in text
        chomp = "-" if trailing == 0 else "" if trailing == 1 else "+"
        body = [indent + line if line else "" for line in text.split("\n")] + [""] * max(trailing - 1, 0)
        return (">" if folded else "|") + chomp, body
    quoted = "double" if dominant == "double" else "single"
    want = style if style != "plain" else "plain" if plain_ok(value) else quoted
    if want == "plain":
        return value, []
    if want == "single" and not any(escaped_char(c) for c in value):
        return "'" + value.replace("'", "''") + "'", []
    return rust_double_quoted(value), []


def scalar_text(value, style):
    head, body = render_scalar(value, style, style, "")
    return head if not body else rust_double_quoted(value)


def block_lines(value, style):
    """En verdi som blokk-YAML på innrykk 0 (`block_lines`)."""
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                out.append(f"{key}:")
                out.extend("  " + line for line in block_lines(item, style))
            else:
                out.append(f"{key}: {scalar_text(item, style)}")
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            for i, line in enumerate(block_lines(item, style)):
                out.append(("- " if i == 0 else "  ") + line)
        return out
    return [scalar_text(value, style)]


def line_start(text, at):
    return text.rfind("\n", 0, at) + 1


def after_line(text, at):
    """Starten på linjen etter den `at` står på."""
    end = text.find("\n", at)
    return len(text) if end < 0 else end + 1


def node_end(text, node):
    """Slutten på det siste tegnet i en node (blanke og linjeskift etter den ikke med)."""
    end = node.end_mark.index
    while end > node.start_mark.index and text[end - 1] in " \t\r\n":
        end -= 1
    return end


def insert_lines(text, pos, lines):
    if pos == len(text) and text and not text.endswith("\n"):
        return text + "\n" + "\n".join(lines)
    return text[:pos] + "\n".join(lines) + "\n" + text[pos:]


def mapping_get(node, key):
    for key_node, value_node in node.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == key:
            return key_node, value_node
    return None, None


def add_key(text, owner, key, value, next_keys, generic=False, at_end=False):
    """`key: value` (en tekst) inn i mappingen `owner`: foran den første av `next_keys` som står på egen linje,
    ellers etter den siste enkle nøkkelen før den første nøstede (`add_key`). `generic`: veien eksporten tar for
    et felt uten egen nøkkel i `LABEL_KEYS` (`Edit::SetBefore`), som skriver i stilen til mappingen."""
    col = owner.start_mark.column
    whole = dominant_style(text)
    block_text = text[owner.start_mark.index : node_end(text, owner)]
    for next_key in next_keys:
        key_node, _ = mapping_get(owner, next_key)
        if key_node is None:
            continue
        start = key_node.start_mark.index
        if key_node.start_mark.column == col and not text[line_start(text, start) : start].strip():
            head, body = render_scalar(value, dominant_style(block_text) if generic else whole, whole, " " * (col + 2))
            return insert_lines(text, line_start(text, start), [" " * col + f"{key}:{' ' if head else ''}{head}"] + body)
        break
    after = None
    for key_node, value_node in owner.value:
        if at_end or not isinstance(value_node, yaml.ScalarNode):
            break
        after = value_node
    head, body = render_scalar(value, dominant_style(block_text) if at_end else whole, whole, " " * (col + 2))
    lines = [" " * col + f"{key}:{' ' if head else ''}{head}"] + body
    if after is None:
        return insert_lines(text, after_line(text, node_end(text, owner)), lines)
    if after.style in ("|", ">"):
        return insert_lines(text, after_line(text, node_end(text, after)), lines)
    return insert_lines(text, after_line(text, node_end(text, after)), lines)


def requote(old, new, quote_all):
    """De nye linjene med tekstverdien i doble anførselstegn under `quoteAllStrings` (`requote_added`)."""
    if not quote_all or old == new:
        return new
    old_lines, new_lines = old.split("\n"), new.split("\n")
    added = [False] * len(new_lines)
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
        if tag in ("insert", "replace"):
            added[j1:j2] = [True] * (j2 - j1)
    out, block = [], None
    for index, line in enumerate(new_lines):
        indent = len(line) - len(line.lstrip(" "))
        if block is not None and (not line.strip() or indent > block):
            out.append(line)
            continue
        block = None
        value = line.strip()
        while value.startswith("- "):
            value = value[2:].lstrip()
        after_key = value.split(": ", 1)[1].lstrip() if ": " in value else value
        if after_key[:1] in ("|", ">"):
            block = indent
        out.append(requote_line(line) if added[index] else line)
    return "\n".join(out)


def requote_line(line):
    at = len(line) - len(line.lstrip(" "))
    while line[at:].startswith("- "):
        at += 2
        at += len(line[at:]) - len(line[at:].lstrip())
    rest = line[at:]
    value_at = at
    if ": " in rest:
        key, value = rest.split(": ", 1)
        if key and all(c.isalnum() or c in "-_." for c in key):
            value_at = at + len(key) + 2 + (len(value) - len(value.lstrip()))
    value = line[value_at:]
    if not value or " #" in value or value[0] in '"[{|>&*!#%@`' or value.endswith(":"):
        return line
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return line
        text = value[1:-1].replace("''", "'")
    elif isinstance(plain_scalar(value), Plain):
        return line
    else:
        text = value
    return line[:value_at] + json.dumps(text, ensure_ascii=False)


# Nøklene Specly skriver i en begrepsfil, i rekkefølgen den skriver dem (alfabetisk).
CONCEPT_KEYS = ("columns", "dataType", "developerNote", "downstreamName", "metadata", "name", "rules", "uuid")


def concept_keys_written(data):
    """Nøklene i begrepsfilen som Specly også skriver for dette begrepet."""
    out = set()
    for key in ("dataType", "developerNote", "downstreamName"):
        if isinstance(data.get(key), str) and data[key]:
            out.add(key)
    if as_map(data.get("metadata")):
        out.add("metadata")
    if [r for r in as_list(data.get("rules")) if isinstance(r, dict)]:
        out.add("rules")
    return out | {"name", "uuid"}


def add_concept_links(front, data, entries):
    """Toppen av en begrepsfil med `entries` lagt inn i `columns` på plassen etter sti, slik eksporten gjør det.
    `None` når listen står slik at eksporten skriver den på en måte sjekken ikke kan forutsi."""
    root = yaml.compose(front, Loader=yaml.SafeLoader) if front.strip() else None
    if root is not None and not isinstance(root, yaml.MappingNode):
        return None
    _, columns = mapping_get(root, "columns") if root is not None else (None, None)
    if columns is None:
        if root is not None and mapping_get(root, "columns")[0] is not None:
            return None  # `columns:` uten verdi: eksporten bytter hele nøkkelen.
        if root is None:
            return None
        style = dominant_style(front[: after_line(front, node_end(front, root))])
        lines = ["columns:"] + ["  " + line for line in block_lines(sorted(entries, key=lambda e: e["path"]), style)]
        written = concept_keys_written(data)
        for key in CONCEPT_KEYS[1:]:
            key_node, _ = mapping_get(root, key)
            if key in written and key_node is not None:
                if key_node.start_mark.column == 0:
                    return insert_lines(front, line_start(front, key_node.start_mark.index), lines)
                return None
        return insert_lines(front, after_line(front, node_end(front, root)), lines)
    if not isinstance(columns, yaml.SequenceNode) or columns.flow_style or not columns.value:
        return None
    for entry in sorted(entries, key=lambda e: e["path"]):
        columns = mapping_get(yaml.compose(front, Loader=yaml.SafeLoader), "columns")[1]
        first = columns.value[0]
        prefix = front[line_start(front, first.start_mark.index) : first.start_mark.index]
        if prefix.strip() != "-":
            return None
        list_text = front[columns.start_mark.index : node_end(front, columns)]
        lines = [(prefix if i == 0 else " " * len(prefix)) + line for i, line in enumerate(block_lines(entry, dominant_style(list_text)))]
        paths = [n.value if isinstance(n, yaml.ScalarNode) else (mapping_get(n, "path")[1].value if isinstance(n, yaml.MappingNode) and mapping_get(n, "path")[1] is not None else "") for n in columns.value]
        before = next((i for i, p in enumerate(paths) if p > entry["path"]), None)
        if before is not None:
            front = insert_lines(front, line_start(front, columns.value[before].start_mark.index), lines)
        else:
            front = insert_lines(front, after_line(front, node_end(front, columns)), lines)
    return front


def add_concept_uuid(front, value):
    """Toppen av en begrepsfil med `uuid` lagt til der eksporten legger den (etter den siste enkle nøkkelen før den første nøstede)."""
    root = yaml.compose(front, Loader=yaml.SafeLoader)
    if not isinstance(root, yaml.MappingNode):
        return None
    return add_key(front, root, "uuid", value, [])


def patch_concept_file(text, data, entries, uuid_value, quote_all):
    """Begrepsfilen med nye lenker og uuid, eller `None` når eksporten ikke kan forutsies."""
    lines = text.split("\n")
    close = next((i for i, line in enumerate(lines[1:], start=1) if line.rstrip() == "---"), None)
    if lines[0].rstrip() != "---" or close is None:
        return None
    front = "".join(line + "\n" for line in lines[1:close])
    new = front
    if entries:
        new = add_concept_links(new, data, entries)
    if new is not None and uuid_value:
        new = add_concept_uuid(new, uuid_value)
    if new is None:
        return None
    new = requote(front, new, quote_all)
    return lines[0] + "\n" + new + "\n".join(lines[close:])


def property_node(text, table, column):
    root = yaml.compose(text, Loader=yaml.SafeLoader)
    schema = mapping_get(root, "schema")[1] if isinstance(root, yaml.MappingNode) else None
    if not isinstance(schema, yaml.SequenceNode) or len(schema.value) <= table.index:
        return None
    props = mapping_get(schema.value[table.index], "properties")[1] if isinstance(schema.value[table.index], yaml.MappingNode) else None
    if not isinstance(props, yaml.SequenceNode) or len(props.value) <= column.index or not isinstance(props.value[column.index], yaml.MappingNode):
        return None
    return props.value[column.index]


def specly_writes(value):
    """Om Specly skriver en nøkkel med denne verdien på en kolonne (den lar tomme verdier og false være)."""
    return value not in (None, False, "", [], {})


def patch_column_texts(text, fills, quote_all):
    """Kontrakten med de arvede tekstene lagt inn på kolonnene, slik eksporten gjør det."""
    order = SHAPES["property"][0]
    new = text
    for column, key, value in fills:
        node = property_node(new, column.table, column)
        if node is None or mapping_get(node, key)[0] is not None:
            return None
        later = order[order.index(key) + 1 :] if key in order else []
        next_keys = [k for k in later if specly_writes(column.prop.get(k))]
        new = add_key(new, node, key, value, next_keys, generic=key != "description")
    return requote(text, new, quote_all)


def patch_flags(text, columns, quote_all):
    """Kontrakten med flaggene reglene setter, slik eksporten skriver dem inn (`node_candidates`, `Edit::SetBefore`): en
    konstruksjonsplass (`primaryKey: true`) eller en ny `tags` foran den neste av Speclys nøkler som kolonnen har og Specly
    skriver (`next_key`), ellers sist i kolonnen (`add_block_key`); en tagg sist i `tags`."""
    order = SHAPES["property"][0]
    new = text
    for column, writes in columns:
        added = set()
        for key, value in writes:
            node = property_node(new, column.table, column)
            if node is None:
                return None
            keys = {k.value for k, _ in node.value if isinstance(k, yaml.ScalarNode)}
            have = keys & (getattr(column, "rendered", set()) | added)
            added.add(key)
            later = order[order.index(key) + 1 :]
            if key == "tags" and "tags" in keys:
                items = mapping_get(node, "tags")[1]
                if not isinstance(items, yaml.SequenceNode) or items.flow_style or not items.value:
                    return None
                # I stilen til det første elementet, etter det siste (`append_item`).
                first, last = items.value[0], items.value[-1]
                start = first.start_mark.index
                prefix = new[line_start(new, start) : start]
                if prefix.strip() != "-" or not isinstance(first, yaml.ScalarNode):
                    return None
                head, body = render_scalar(value, style_of(new[start:]) if first.style else "plain", dominant_style(new), "")
                if body:
                    return None
                new = insert_lines(new, after_line(new, node_end(new, last)), [prefix + head])
                continue
            value = [value] if key == "tags" else value
            nxt = next((k for k in later if k in have), None)
            key_node = mapping_get(node, nxt)[0] if nxt else None
            col = node.start_mark.column
            if key_node is not None and key_node.start_mark.column == col and not new[line_start(new, key_node.start_mark.index) : key_node.start_mark.index].strip():
                new = add_key(new, node, key, value, [nxt], generic=True)
            else:
                # Ingen slik nøkkel (eller den står ikke på egen linje): sist i kolonnen (`add_block_key`).
                new = add_key(new, node, key, value, [], generic=True, at_end=True)
    return requote(text, new, quote_all)


def reorder_properties(text, table, order):
    """Kolonnene i tabellen i rekkefølgen `order` (plassene i filen), slik eksporten flytter dem (`reorder_items`): hver
    kolonne flyttes hel, fra starten på linjen med `-` til slutten av det siste den har; det som står mellom kolonnene, står."""
    root = yaml.compose(text, Loader=yaml.SafeLoader)
    schema = mapping_get(root, "schema")[1] if isinstance(root, yaml.MappingNode) else None
    if not isinstance(schema, yaml.SequenceNode) or len(schema.value) <= table.index or not isinstance(schema.value[table.index], yaml.MappingNode):
        return None
    props = mapping_get(schema.value[table.index], "properties")[1]
    if not isinstance(props, yaml.SequenceNode) or props.flow_style or len(props.value) != len(order) or not all(isinstance(p, yaml.MappingNode) and not p.flow_style for p in props.value):
        return None
    spans = [(line_start(text, p.start_mark.index), node_end(text, p)) for p in props.value]
    out = text
    for k in range(len(spans) - 1, -1, -1):
        start, end = spans[k]
        from_start, from_end = spans[order[k]]
        out = out[:start] + text[from_start:from_end] + out[end:]
    return out


# ---------- JSON Schema (det skjemaene i .specly/schemas bruker) ----------


def validate(value, schema, root, pointer):
    """Gir `(peker, kode, melding)` for hvert brudd; koden er `schema.` og nøkkelordet."""
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            target = target.get(part, {})
        yield from validate(value, target, root, pointer)
        return
    if "anyOf" in schema:
        if all(list(validate(value, option, root, pointer)) for option in schema["anyOf"]):
            yield pointer, "schema.anyOf", "passer ikke med noen av de tillatte formene"
        return
    expected = schema.get("type")
    if expected is not None:
        types = expected if isinstance(expected, list) else [expected]
        if not any(has_type(value, t) for t in types):
            yield pointer, "schema.type", f"skal være {' eller '.join(types)}"
            return
    if "enum" in schema and value not in schema["enum"]:
        yield pointer, "schema.enum", f"skal være en av {', '.join(map(str, schema['enum']))}"
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                yield pointer, "schema.required", f"mangler {key}"
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            if item is None:
                continue  # Specly leser en tom verdi som om nøkkelen mangler.
            if key in properties:
                yield from validate(item, properties[key], root, f"{pointer}/{key}")
            elif extra is False:
                yield f"{pointer}/{key}", "schema.additionalProperties", "er ikke et kjent felt"
            elif isinstance(extra, dict):
                yield from validate(item, extra, root, f"{pointer}/{key}")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            yield from validate(item, schema["items"], root, f"{pointer}/{index}")


def has_type(value, name):
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "array":
        return isinstance(value, list)
    if name == "object":
        return isinstance(value, dict)
    return True


# ---------- Kommandoer ----------


def code_matches(code, pattern):
    """Et mønster treffer koden selv, eller koder det er et prefiks til ved et punktum: `lint.enum` (og `lint.enum.`,
    `lint.enum.*`) treffer `lint.enum.flag`, men ikke `lint.enumx`."""
    pattern = pattern.removesuffix("*").removesuffix(".")
    return code == pattern or code.startswith(pattern + ".")


def check_patterns(patterns, where):
    """Stopper (exit 2) på et tomt mønster eller et som ingen kode sjekken kjenner treffer: ellers ville en skrivefeil gjort bygget grønt."""
    for pattern in patterns:
        if not pattern.removesuffix("*").removesuffix("."):
            raise Stop(f"{where}: en tom kode. Skriv en kode som lint.uuid.missing, eller et prefiks som lint.enum.")
        if not any(code_matches(code, pattern) for code in CODES):
            close = difflib.get_close_matches(pattern.removesuffix("*").removesuffix("."), CODES, n=3)
            hint = f" Mente du {' eller '.join(close)}?" if close else " Kodene står i hver melding fra check, og i --json."
            raise Stop(f"{where}: {pattern} er ingen kode sjekken melder, og ingen kode starter med {pattern}.{hint}")


class Policy:
    """Funnene som stopper en PR (`failOn`) og dem som ikke vises (`ignore`): `.specly/check.json`, så kommandolinjen.
    Står samme kode i begge, vinner failOn: det et team uttrykkelig har bedt om å stoppe på, skjules ikke."""

    def __init__(self, args):
        path = Path(__file__).resolve().parent / CHECK_CONFIG
        config = {}
        if path.exists():
            try:
                config = json.loads(path.read_bytes().decode("utf-8-sig"))
            except OSError as e:
                raise Stop(f"{path} kan ikke leses ({e.strerror or e}). Den skal være en fil.")
            except ValueError as e:
                raise Stop(f"{path} er ikke gyldig JSON ({e}).")
            lists = ("failOn", "ignore")
            if not isinstance(config, dict) or set(config) - set(lists) or not all(isinstance(config.get(k, []), list) and all(isinstance(v, str) for v in config.get(k, [])) for k in lists):
                raise Stop(f'{path} skal være et JSON-objekt med bare listene "failOn" og "ignore", med koder som tekst, f.eks. {{"failOn": ["lint.uuid.missing"], "ignore": ["lint.column.noDescription"]}}.')
            for key in lists:
                check_patterns(config.get(key, []), f"{path} ({key})")
        check_patterns(getattr(args, "fail_on", None) or [], "--fail-on")
        check_patterns(getattr(args, "ignore", None) or [], "--ignore")
        self.fail_on = config.get("failOn", []) + (getattr(args, "fail_on", None) or [])
        self.ignore = config.get("ignore", []) + (getattr(args, "ignore", None) or [])

    def failed(self, item):
        return any(code_matches(item["rule"], p) for p in self.fail_on)

    def ignored(self, item):
        if self.failed(item):
            return False
        # En feil (noe Specly ikke kan lese inn) skjules bare når koden står med hele navnet, aldri av et prefiks.
        if item["level"] == "error":
            return item["rule"] in self.ignore
        return any(code_matches(item["rule"], p) for p in self.ignore)

    def apply(self, items):
        """Funnene uten de ignorerte, med `failOn`-funnene som feil; og antallet som ble ignorert."""
        kept = []
        for item in items:
            if self.ignored(item):
                continue
            if item["level"] != "error" and self.failed(item):
                item = {**item, "level": "error", "failOn": True}
            kept.append(item)
        return kept, len(items) - len(kept)


def unborn_repo(repo):
    """Et git-repo uten én commit: ingenting fra det kan være lest inn i Specly."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=repo.top, capture_output=True).returncode
    return git("symbolic-ref", "--quiet", "HEAD") == 0 and git("rev-parse", "--verify", "--quiet", "HEAD") != 0


def run_check(args, overrides=None):
    findings = Findings()
    repo = Repo(Path(__file__).resolve().parent.parent, findings, overrides)
    repo.load()
    baseline = Baseline(repo, args.changed_from) if args.changed_from else None
    check = Check(repo, baseline, args.lineage_required, not getattr(args, "no_format", False), getattr(args, "strict", False))
    check.baseline_ref = args.changed_from
    # Med --ignore format.differs skriver fix ikke en tags-liste i flytstil om til blokkform, så et nytt flagg der skriver den ikke.
    check.format_ignored = Policy(args).ignored({"rule": "format.differs", "level": "warning"})
    check.run()
    items = findings.items
    if baseline:
        items = [i for i in items if i["file"] in baseline.changed or any(r in baseline.changed for r in i["related"])]
    items.sort(key=lambda i: (i["file"], i["line"], i["rule"], i["message"]))
    return repo, check, items


def command_check(args):
    policy = Policy(args)
    _, check, items = run_check(args)
    visible = {id(i) for i in items if not policy.ignored(i)}
    items, ignored = policy.apply(items)
    errors = [i for i in items if i["level"] == "error"]
    warnings = [i for i in items if i["level"] == "warning"]
    promoted = sum(1 for i in errors if i.get("failOn"))
    if args.json:
        strip = lambda i: {k: i[k] for k in ("file", "line", "rule", "message", "failOn") if k in i}
        result = {"ok": not errors, "errors": [strip(i) for i in errors], "warnings": [strip(i) for i in warnings]}
        if check.skipped:
            result["skipped"] = check.skipped
        if policy.fail_on:
            result["failOn"] = policy.fail_on
        if policy.ignore:
            result["ignored"] = {"codes": policy.ignore, "count": ignored}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        shown = errors + ([] if args.errors_only else warnings)
        per_file = {}
        lines = []
        # Det reglene ville endret, vises som én linje per kode når det er mange: et repo der reglene aldri er kjørt,
        # ville ellers fått en linje for hver tabell. --verbose og --json har hvert funn.
        # Også når koden står i --fail-on (en PR-bygg ville ellers fått tusenvis av linjer); avslutningskoden er den samme.
        many = {code for code in SUMMARISED if not args.verbose and sum(1 for i in shown if i["rule"] == code) > SUMMARY_LIMIT}
        summarised = {}
        for item in shown:
            if item["rule"] in many:
                if item["rule"] not in summarised:
                    summarised[item["rule"]] = {"first": item, "count": 0}
                    lines.append(item["rule"])
                summarised[item["rule"]]["count"] += 1
                continue
            if item["rule"] == NO_DESCRIPTION and not args.verbose and item["level"] == "warning":
                if item["file"] not in per_file:
                    per_file[item["file"]] = {"first": item["line"], "count": 0}
                    lines.append(item["file"])
                per_file[item["file"]]["count"] += 1
                continue
            label = "" if item["level"] == "error" else "advarsel  "
            lines.append(f"{item['file']}:{item['line']}  {label}{item['rule']}  {item['message']}")
        for line in lines:
            if line in summarised:
                n = summarised[line]
                first = n["first"]
                label = "" if first["level"] == "error" else "advarsel  "
                failed_note = " (feil fra --fail-on)" if first["level"] == "error" else ""
                print(f"{first['file']}:{first['line']}  {label}{line}  {n['count']} funn{failed_note}: {SUMMARISED[line]} Det første: {first['message']} Vis hvert med --verbose.")
            elif line in per_file:
                n = per_file[line]
                print(f"{line}:{n['first']}  advarsel  {NO_DESCRIPTION}  {n['count']} {'kolonne mangler' if n['count'] == 1 else 'kolonner mangler'} description (den første på linje {n['first']}). Vis hver med --verbose.")
            else:
                print(line)
        for note in check.skipped:
            print(f"hoppet over: {note}", file=sys.stderr)
        missing = sum(i["rule"] == NO_DESCRIPTION for i in warnings)
        extra = f" (av dem mangler {missing} kolonner description; --verbose viser hver)" if missing and not args.verbose and not args.errors_only else ""
        failed = f" ({promoted} av dem fra --fail-on)" if promoted else ""
        hidden = f", {ignored} ignorert" if ignored else ""
        print(f"{len(errors)} feil{failed}, {len(warnings)} advarsler{extra}{hidden}", file=sys.stderr)
        rule_files = rules_to_apply(check, visible)
        if rule_files and not args.errors_only:
            print(rules_hint(len(rule_files)), file=sys.stderr)
    return 1 if errors else 0


# Registerfilene `fix --add-values` skriver i, og navnet Specly lager uuid-en til en oppføring uten under (`entry_uuid`).
REGISTRY_KINDS = {
    "datatypes.json": "dataTypes",
    "flags.json": "flags",
    "table_statuses.json": "tableStatuses",
    "column_statuses.json": "columnStatuses",
    "table_types.json": "tableTypes",
    "source_systems.json": "sourceSystems",
}


def registry_entry(registry, name):
    """En ny oppføring slik Specly skriver den (`registry_entry` i build.rs): uuid laget av navnet, name, tom
    description, og for en tabelltype feltene og listene den alltid skriver."""
    entry = {"uuid": str(uuidlib.uuid5(ENTRY_UUID_NS, f"{REGISTRY_KINDS[registry]}:{name}")), "name": name, "description": ""}
    if registry == "table_types.json":
        entry.update(regexPattern="", columnTemplates=[], columnFieldDefUuids=[], columnFields=[], metadataFieldDefUuids=[], tableFields=[])
    return entry


def insert_entry(entries, entry):
    """Legger `entry` der Specly sorterer den (`sort_registry_entries`): oppføringer med `order`/`sortOrder`/`priority`
    først, så etter uuid. En ny oppføring har ingen rekkefølge, så den står blant dem uten, etter uuid."""
    has_order = lambda e: isinstance(e, dict) and any(is_number(e.get(k)) for k in ("order", "sortOrder", "priority"))
    uuid_of = lambda e: e.get("uuid") if isinstance(e, dict) and isinstance(e.get("uuid"), str) else ""
    at = next((i for i, e in enumerate(entries) if not has_order(e) and uuid_of(e) > entry["uuid"]), len(entries))
    entries.insert(at, entry)


def rules_to_apply(check, kept):
    """Kontrakt -> (flagg, kolonnerekkefølger) `fix --apply-rules` skriver, for funnene som er med (`kept`)."""
    out = {}
    for path, entries in check.flag_writes.items():
        flags = [(c, w) for c, w, item in entries if id(item) in kept and w]
        if flags:
            out.setdefault(path, ([], []))[0].extend(flags)
    for path, entries in check.column_orders.items():
        orders = [(t, o) for t, o, item in entries if id(item) in kept]
        if orders:
            out.setdefault(path, ([], []))[1].extend(orders)
    return out


def rules_hint(count):
    return f"fix --apply-rules ville endret {count} {'kontrakt' if count == 1 else 'kontrakter'}: flaggene og kolonnerekkefølgen en kjøring av reglene i Specly gir (rules.*). Reglene kjører aldri av seg selv i Specly, så fix skriver dem bare når det er bedt om."


class FixPass:
    """Det én runde av fix vil skrive, regnet over tekstene fra rundene før."""

    def __init__(self):
        self.texts = {}  # sti -> ny tekst (LF)
        self.notes = {}  # sti -> hva som er gjort
        self.kinds = {}  # sti -> hva slags skriving (format, concept, fills, rules, ids, values, lint)
        self.blocked = {}  # sti -> hvorfor noe fix skulle skrive i filen, ikke ble skrevet
        self.skipped = []
        self.additions = {}
        self.rule_files = {}
        self.hint = 0


def mint_id(project_id, contract, *names):
    """Id-en Specly gir en tabell eller kolonne uten uuid når den leser filen (`resolve_id`/`mint` i odcs_import.rs):
    uuid v5 i navnerommet prosjekt-id-en, av kontraktens `id`, tabellnavnet og kolonnenavnet skilt med \x1f."""
    try:
        namespace = uuidlib.UUID(project_id)
    except ValueError:
        namespace = uuidlib.uuid5(uuidlib.NAMESPACE_URL, project_id)
    raw = contract.get("id")
    contract_id = "" if raw is None else ("true" if raw is True else "false" if raw is False else str(raw))
    return str(uuidlib.uuid5(namespace, "\x1f".join([contract_id, *names])))


def id_plan(repo, check):
    """Kontrakt -> ([(tabell, kolonne eller None, id)], hvorfor ikke) for tabeller og kolonner uten id som er nye i branchen
    (`fix --add-ids`); uten base (repo uten commits) hver tabell og kolonne uten id. En tabell eller kolonne som hadde id i basen, får den tilbake; en kolonne som ikke kan skilles fra
    en som mistet id-en (basen har en kolonne med id som er borte), gir ingen id."""
    b, project = check.baseline, str(repo.settings.manifest.get("projectId") or "")
    unborn = b is None  # repo uten commits: ingenting er i Specly ennå, så alt uten id er nytt
    out = {}
    table_ids = {t.id.lower() for t in repo.tables if t.id}
    for table in repo.tables:
        if table.unreadable or table.ghost or (not unborn and table.file not in b.changed) or not table.name:
            continue
        path = repo.top / table.file
        writes, why = out.setdefault(path, ([], []))
        old = None if unborn else check.old_table(table)
        if not table.id and "id" not in table.obj:
            # Tabellene filen hadde i basen med en id som er borte (ikke på id, ikke på navn): en av dem kan være denne,
            # med nytt navn, og det avgjør ikke filene.
            here_names = {t.name.lower() for t in repo.tables if t.file == table.file}
            gone_tables = {} if unborn else {id(t): t for t in b.old_tables.values() if t.file == table.file and t.id and t.id.lower() not in table_ids and t.name.lower() not in here_names}
            if old is not None and old.id and old.id.lower() not in table_ids:
                writes.append((table, None, old.id))
            elif old is not None:
                pass  # uten id i basen også: ikke ny i branchen, Specly kjenner den på navnet med sin egen uuid
            elif gone_tables:
                first = next(iter(gone_tables.values()))
                why.append(f"tabellen {table.name} har ingen id, og {first.name} hadde id i {check.baseline_ref} og er borte fra filen; om det er samme tabell med nytt navn, avgjør ikke filene. Er det den samme, skriv id-en den hadde ({first.id}); er den ny, gi den en id selv")
                continue
            else:
                writes.append((table, None, mint_id(project, table.contract, table.name)))
        here = {c.id.lower() for c in table.columns if c.id}
        gone = [c for c in old.columns if c.id and c.id.lower() not in here and table.column(c.name) is None] if old is not None else []
        for column in table.columns:
            if column.id or "id" in column.prop or not column.name:
                continue
            before = old.column(column.name) if old is not None else None
            if before is not None:
                if before.id and before.id.lower() not in here:
                    writes.append((table, column, before.id))
                continue  # uten id i basen også: ikke ny i branchen, Specly kjenner den på navnet
            if gone:
                why.append(f"{table.name}.{column.name} har ingen id, og {', '.join(c.name for c in gone)} hadde id i {check.baseline_ref} og er borte; om det er samme kolonne med nytt navn, avgjør ikke filene. Er det den samme, skriv id-en den hadde ({gone[0].id}); er den ny, gi den en id selv")
                continue
            writes.append((table, column, mint_id(project, table.contract, table.name, column.name)))
    return {p: (w, why) for p, (w, why) in out.items() if w or why}


def add_first_key(text, owner, key, value, quote_all):
    """`key: value` først i mappingen `owner` (der Specly skriver `id`), i filens stil, eller `None` i flytstil."""
    if not isinstance(owner, yaml.MappingNode) or owner.flow_style or not owner.value:
        return None
    first = owner.value[0][0]
    at = first.start_mark.index
    whole = dominant_style(text)
    head, _ = render_scalar(value, whole, whole, "")
    new = text[:at] + f"{key}: {head}\n" + " " * first.start_mark.column + text[at:]
    return requote(text, new, quote_all)


def patch_ids(text, writes, quote_all):
    new = text
    for table, column, value in writes:
        if column is None:
            root = yaml.compose(new, Loader=yaml.SafeLoader)
            schema = mapping_get(root, "schema")[1] if isinstance(root, yaml.MappingNode) else None
            node = schema.value[table.index] if isinstance(schema, yaml.SequenceNode) and len(schema.value) > table.index else None
        else:
            node = property_node(new, table, column)
        new = add_first_key(new, node, "id", value, quote_all) if node is not None else None
        if new is None:
            return None
    return new


def plan_fix(args, policy, repo, check, items, frozen):
    """Det fix skriver i én runde, over tekstene repoet har nå. Filene i `frozen` rører den ikke. Formatet skrives bare
    i en fil fix ikke har skrevet i en runde før: det reglene skrev slik eksporten skriver det (et nytt flagg sist i en
    kolonne), står slik eksporten setter det."""
    out = FixPass()
    kept = {id(i) for i in items}  # med --changed-from: bare funnene endringene fører til
    format_ignored = policy.ignored({"rule": "format.differs", "level": "warning"})
    changed = check.baseline.changed if check.baseline else None
    # Filer med feil av sine egne, eller der en nøkkel står to ganger: der skriver fix bare formatet. En verdi uten
    # anførselstegn (`yaml.ambiguousPlain`) setter fix dem rundt, så den står ikke i veien.
    with_errors = {i["file"] for i in check.f.items if i["level"] == "error" and i["rule"] != "yaml.ambiguousPlain"} | {repo.rel(p) for p in repo.broken_yaml}
    plan = {}  # path -> {"format": tekst eller None, "quoted", "kind", "concept", "links", "uuid", "fills", "flags", "orders", "ids"}
    for path, (text, wanted, kind) in check.reformatted.items():
        if format_ignored or (changed is not None and repo.rel(path) not in changed) or path in repo.overrides:
            continue
        # Registeret skriver formatsjekken om linje for linje (bare anførselstegnene): kommentarene står.
        if kind != "registry" and has_comments(text, kind):
            out.skipped.append(f"{repo.rel(path)}  ikke rettet: filen har kommentarer, og Specly skriver ikke kommentarer. Fjern dem eller flytt teksten til description.")
            continue
        plan.setdefault(path, {})["format"] = wanted
    # Anførselstegn rundt verdiene en YAML 1.1-leser leser som noe annet, og ikke noe annet i filen. Formatet Specly
    # skriver filen i, har dem allerede.
    for path, spots in check.ambiguous.items():
        spots = [s for s in spots if id(s[4]) in kept]
        if not spots or plan.get(path, {}).get("format") is not None:
            continue
        text = repo.read_text(path)
        bom = "﻿" if text.startswith("﻿") else ""
        lines = text[len(bom) :].split("\n")
        for line, start, end, quoted, _ in sorted(spots, key=lambda s: (s[0], s[1]), reverse=True):
            lines[line] = lines[line][:start] + quoted + lines[line][end:]
        plan.setdefault(path, {}).update(quoted=bom + "\n".join(lines), count=len(spots))
    for path, (concept, entries) in check.concept_writes.items():
        links = [e for e, item in entries if id(item) in kept]
        if links:
            plan.setdefault(path, {}).update(kind="concept", concept=concept, links=links)
    for path, (concept, value, item) in check.concept_uuids.items():
        if id(item) in kept:
            plan.setdefault(path, {}).update(kind="concept", concept=concept, uuid=value)
    for path, fills in check.column_texts.items():
        fills = [(c, k, v) for c, k, v, item in fills if id(item) in kept]
        if fills:
            plan.setdefault(path, {}).update(kind="contract", fills=fills)
    # Det reglene gir, bare når det er bedt om (`--apply-rules`): reglene kjører aldri av seg selv i Specly.
    out.rule_files = rules_to_apply(check, kept)
    for path, (flags, orders) in out.rule_files.items() if args.apply_rules else []:
        if flags:
            plan.setdefault(path, {}).update(kind="contract", flags=flags)
        if orders:
            plan.setdefault(path, {}).update(kind="contract", orders=orders)
    for path, (writes, why) in id_plan(repo, check).items() if args.add_ids else []:
        step = plan.setdefault(path, {})
        step.update(kind="contract", ids=writes)
        if why:
            step["undecided"] = why
    for path, step in sorted(plan.items()):
        rel = repo.rel(path)
        if path in frozen:
            out.skipped.append(f"{rel}  ikke rettet: {frozen[path]}. fix skriver ingenting i filen, så den ikke blir halvveis rettet; rett det, og kjør fix igjen")
            continue
        text = step.get("format")
        notes, kinds = [], set()
        if text is not None:
            notes.append("skrevet i Specly-format")
            kinds.add("format")
        elif "quoted" in step:
            text = step["quoted"]
            notes.append(f"satte anførselstegn rundt {step['count']} {'verdi' if step['count'] == 1 else 'verdier'} en YAML 1.1-leser leser som noe annet enn tekst")
            kinds.add("quotes")
        if "kind" in step:
            base = text if text is not None else repo.texts.get(path) or ""
            base = base[1:] if base.startswith("\ufeff") else base
            why = None
            if step.get("undecided"):
                why = "; ".join(step["undecided"])
            elif rel in with_errors:
                why = "filen har feil (se check); rett dem først"
            elif has_comments(base, step["kind"]):
                why = "filen har kommentarer"
            else:
                done, did = [], set()
                if step["kind"] == "concept":
                    patched = patch_concept_file(base, step["concept"].data, step.get("links", []), step.get("uuid"), repo.settings.quote_all)
                    done = [f"la til lenken {e['path']}" for e in step.get("links", [])] + ([f"la til uuid {step['uuid']}"] if step.get("uuid") else [])
                    did.add("concept")
                else:
                    patched = base
                    if step.get("ids"):
                        patched = patch_ids(patched, step["ids"], repo.settings.quote_all)
                        done += [f"la til id {value} på {table.name}" + (f".{column.name}" if column else "") for table, column, value in step["ids"]]
                        did.add("ids")
                    if patched is not None and step.get("fills"):
                        patched = patch_column_texts(patched, step["fills"], repo.settings.quote_all)
                        done += [f"la til {key} på {column.table.name}.{column.name}" for column, key, _ in step["fills"]]
                        did.add("fills")
                    if patched is not None and step.get("flags"):
                        patched = patch_flags(patched, step["flags"], repo.settings.quote_all)
                        done += [f"la til flagg fra flaggreglene på {column.table.name}.{column.name}" for column, _ in step["flags"]]
                        did.add("rules")
                    for table, order in step.get("orders", []) if patched is not None else []:
                        patched = reorder_properties(patched, table, order)
                        done.append(f"flyttet kolonnene i {table.name} slik kolonnesorteringsreglene gir dem")
                        did.add("rules")
                        if patched is None:
                            break
                if patched is None:
                    why = "filen står slik at sjekken ikke kan si nøyaktig hvordan Specly skriver det inn"
                else:
                    text = patched
                    notes.extend(done)
                    kinds |= did
            if why:
                # En fil som får tekst i denne runden, sjekkes på nytt i neste: der går det inn, eller filen får ingenting.
                out.blocked[path] = why
                if text is None:
                    notes.append(f"det reglene gir (begrepslenker, arvet tekst, flagg, kolonnerekkefølge, id-er) ikke lagt inn: {why}. Skriv det check melder for hånd")
        if text is not None:
            out.texts[path] = text
            out.notes[path] = notes
            out.kinds[path] = kinds
        elif notes:
            out.skipped.append(f"{rel}  " + "; ".join(notes))
    # Verdier som mangler i et register, når de er bedt om (`--add-values`) og ikke er ignorert.
    for registry, names in sorted(check.missing_values.items()):
        wanted = sorted(n for n, found in names.items() if any(id(i) in kept for i in found))
        if wanted and args.add_values and registry in REGISTRY_KINDS:
            out.additions[registry] = wanted
    # Verdiene som mangler, bare dem som ikke er ignorert og som endringene fører til (--changed-from).
    out.hint = 0 if args.add_values else sum(1 for names in check.missing_values.values() for found in names.values() if any(id(i) in kept for i in found))
    for registry, names in out.additions.items():
        path = repo.registry_path(registry)
        yaml_file = path.suffix == ".yaml"
        if yaml_file:
            # Verdiene slik formatsjekken leser dem (tall og true står som de er), så de skrives tilbake uendret.
            node = yaml.compose(repo.read_text(path) or "", Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader)) if path.is_file() else None
            entries = as_list(specly_value(node)) if node is not None else []
        else:
            entries = as_list(repo.read_json(path, []))
        for name in names:
            insert_entry(entries, registry_entry(registry, name))
        # YAML slik Specly skriver kildesystemene (`to_yaml` i build.rs), ellers JSON.
        # Med anførselstegn når filen har det fra før.
        first = next((line for line in (repo.read_text(path) or "").splitlines() if line.startswith("- ")), "") if yaml_file and path.is_file() else ""
        quoted = (split_value(first[2:])[1] or "").startswith('"')
        out.texts[path] = render_yaml(entries, quoted) if yaml_file else json.dumps(js_numbers(entries), indent=2, ensure_ascii=False)
        out.notes[path] = [f"la til {', '.join(names)}"]
        out.kinds[path] = {"values"}
    # Specly skriver navnelistene i .specly/lint.json på nytt ved eksporten etter innhentingen: med navnene der
    # allerede endrer den ikke filen.
    enum_keys = {"datatypes.json": ["dataTypes"], "flags.json": ["flags"]}
    for level, used in check.status_used.items():
        enum_keys.setdefault(used, []).append(f"{level}Statuses")
    lint_path = repo.root / ".specly/lint.json"
    lint = repo.read_json(lint_path, None)
    enums = lint.get("enums") if isinstance(lint, dict) else None
    grown = False
    for registry, names in out.additions.items():
        for key in enum_keys.get(registry, []) if isinstance(enums, dict) else []:
            if isinstance(enums.get(key), list):
                new = [n for n in names if n not in enums[key]]
                enums[key] = sorted(enums[key] + new)
                grown = grown or bool(new)
    if grown:
        out.texts[lint_path] = json.dumps(js_numbers(lint), indent=2, ensure_ascii=False) + "\n"
        out.notes[lint_path] = ["la til navnene i enums, slik Specly skriver dem etter innhentingen"]
        out.kinds[lint_path] = {"lint"}
    return out


FIX_PASSES = 8


def command_fix(args):
    """fix i runder: hver runde kjører hele sjekken over tekstene rundene før skrev, så det en rettet feil sto i veien for
    (et YAML-anker, tags i flytstil), skrives i samme kjøring. En fil der noe fix skulle skrive, fortsatt ikke kan skrives
    (feil, kommentarer), får ingenting: den legges tilbake slik den står på disk, og rundene kjøres på nytt uten den.
    Ingenting skrives før rundene er ferdige."""
    policy = Policy(args)
    overrides, frozen, notes, kinds = {}, {}, {}, {}
    for _ in range(FIX_PASSES):
        repo, check, items = run_check(args, overrides)
        if args.add_ids and not args.changed_from and not unborn_repo(repo):
            raise Stop("fix --add-ids trenger --changed-from <ref>: basen avgjør hvilke tabeller og kolonner som er nye i branchen, og hvilke som hadde en id som må tilbake. Uten den kunne fix gitt en tabell Specly alt kjenner på navnet en annen id enn den har. Kjør: fix --add-ids --changed-from origin/<branchen den skal inn i>. Uten base går --add-ids bare i et repo uten commits.")
        if args.add_ids and repo.settings.shorthand:
            raise Stop("fix --add-ids: repoet bruker kort form (referenceStyle: shorthand i odcs.json), og der skriver Specly ingen id-er.")
        if args.add_ids and not repo.settings.manifest.get("projectId"):
            raise Stop(f"fix --add-ids: {repo.rel(repo.root / '.specly.json')} har ingen projectId, så id-ene Specly ville laget kan ikke regnes ut. Gjør en skriving fra Specly til branchen.")
        step = plan_fix(args, policy, repo, check, [i for i in items if not policy.ignored(i)], frozen)
        new = {p: t for p, t in step.texts.items() if t != repo.read_text(p)}
        stuck = {p: why for p, why in step.blocked.items() if p in overrides and p not in new and p not in frozen}
        if stuck:
            frozen.update(stuck)
            for p in stuck:
                overrides.pop(p)
                notes.pop(p, None)
                kinds.pop(p, None)
            continue
        if not new:
            break
        overrides.update(new)
        for p in new:
            notes.setdefault(p, []).extend(n for n in step.notes[p] if n not in notes.get(p, []))
            kinds.setdefault(p, set()).update(step.kinds[p])
        # En ny runde bare når den kan gi noe: en fil der noe sto i veien, eller (med --apply-rules) det reglene skrev
        # eller verdiene som kom til, som reglene leser. Bare formatet gir aldri noe nytt å skrive.
        if not any(p in step.blocked for p in new) and not (args.apply_rules and any(step.kinds[p] - {"format", "quotes", "lint"} for p in new)):
            break
    else:
        raise Stop(f"fix kom ikke til ro etter {FIX_PASSES} runder (hver runde ville skrevet noe nytt). Ingenting er skrevet. Meld det til Specly.")
    disk = Repo(repo.root, Findings())
    final = {p: t for p, t in overrides.items() if t != disk.read_text(p)}
    count_of = lambda kind: sum(1 for p in final if kind in kinds.get(p, set()))
    described = [
        (count_of("format"), "i Specly-format"),
        (count_of("quotes"), "med anførselstegn rundt verdier en YAML 1.1-leser leser som noe annet enn tekst"),
        (count_of("concept"), "begrepsfiler med nye lenker eller uuid"),
        (count_of("fills"), "kontrakter med tekst fra begreper"),
        (count_of("rules"), "kontrakter med flagg eller kolonnerekkefølge fra reglene"),
        (count_of("ids"), "kontrakter med nye id-er"),
    ]
    added = [f"{repo.rel(p)} med nye verdier" for p in final if "values" in kinds.get(p, set())] + [f"{repo.rel(p)} med navnene" for p in final if "lint" in kinds.get(p, set())]
    count = len(final)
    changed = check.baseline.changed if check.baseline else None
    summary = f"fix skriver {count} {'fil' if count == 1 else 'filer'}: " + ", ".join([f"{n} {what}" for n, what in described if n] + added)
    summary += f" (bare det endringene siden {args.changed_from} fører til)." if changed is not None else ". --changed-from <ref> begrenser det til det en branch endrer."
    print(summary if count else "Ingenting å rette.", file=sys.stderr if not count else sys.stdout)
    if step.rule_files and not args.apply_rules:
        print(rules_hint(len(step.rule_files)), file=sys.stderr)
    if step.hint:
        print(f"{step.hint} verdier kontraktene bruker mangler i et register (lint.enum.*). fix legger dem ikke til av seg selv, så en skrivefeil ikke blir en ny verdi: rett navnene, eller kjør fix --add-values.", file=sys.stderr)
    for line in step.skipped:
        print(line)
    common = repo.common_eol()
    for path in sorted(final):
        if not args.dry_run:
            # Til målet for en symbolsk lenke (lenken står), og bare i en fil vi har lov å skrive i.
            target = Path(os.path.realpath(path))
            if not os.access(target, os.W_OK):
                print(f"{repo.rel(path)}  ikke skrevet: filen er skrivebeskyttet. Gjør den skrivbar og kjør fix igjen.")
                continue
            # Via en midlertidig fil med filens egne rettigheter: et avbrudd etterlater den gamle eller den nye filen, aldri
            # en halvskrevet. Navnet er en skjult fil uten noen av repoets endelser (.yaml, .md, .json), som Specly ikke leser;
            # den slettes ved enhver feil, også Ctrl-C.
            temp = target.with_name(f".{target.name}.specly-fix-tmp~")
            try:
                temp.write_bytes(final[path].replace("\n", disk.eol(path, common)).encode("utf-8"))
                shutil.copymode(target, temp)
                os.replace(temp, target)
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        print(f"{repo.rel(path)}  {'; '.join(notes.get(path, []))}")
    return 0


EXIT_CODES = """exit-koder:
  0  ingen feil (advarsler stopper ikke)
  1  feil: noe Specly ikke kan lese inn, eller et funn som --fail-on / failOn i .specly/check.json gjør til feil
  2  sjekken kunne ikke kjøre: ukjent ref, grunt utsjekk uten felles forfader, git feilet, pyyaml mangler,
     Python eldre enn 3.9, .specly.json mangler eller er ødelagt, .specly/check.json er ødelagt eller ingen fil,
     en kode i --fail-on, --ignore eller check.json som ingen kode treffer, eller en feil i skriptet (--verbose viser sporet)

.specly/check.json (teamets fil, Specly skriver den aldri):
  {"failOn": ["lint.uuid.missing", "lint.enum"], "ignore": ["lint.column.noDescription"]}
En kode treffer seg selv og kodene den er et prefiks til ved et punktum (lint.enum treffer lint.enum.flag).
Står en kode i både failOn og ignore, vinner failOn. En feil skjules bare av hele koden.
"""


def main():
    # Skriv UTF-8 også i en Windows-konsoll (cp1252) og med LC_ALL=C, så æøå kommer riktig ut.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sjekker at repoet kan leses inn i Specly.", epilog=EXIT_CODES, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="sjekk hele repoet")
    check.add_argument("--changed-from", metavar="REF", help="vis bare funn i filer endret siden REF, og i filer som peker på dem")
    check.add_argument("--json", action="store_true", help="skriv resultatet som JSON")
    check.add_argument("--errors-only", action="store_true", help="ikke vis advarsler")
    check.add_argument("--no-format", action="store_true", help="ikke sjekk formatet")
    check.add_argument("--strict", action="store_true", help="en fil som ikke står i Specly-format er en feil, ikke en advarsel")
    check.add_argument("--verbose", action="store_true", help="vis hver kolonne uten description, ikke bare antallet per fil")
    check.add_argument("--lineage-required", metavar="PREFIKS", action="append", default=[], help="advar om kolonner uten kilde i tabeller som starter med PREFIKS (kan gjentas)")
    check.add_argument("--fail-on", metavar="KODE", action="append", default=[], help="funn med denne koden er feil (exit 1); KODE er en hel kode (lint.uuid.missing) eller et prefiks ved et punktum (lint.enum). Kan gjentas, legges til failOn i .specly/check.json")
    check.add_argument("--ignore", metavar="KODE", action="append", default=[], help="ikke vis eller tell funn med denne koden (samme form som --fail-on). En feil skjules bare når hele koden står, og en kode i failOn vinner. Kan gjentas, legges til ignore i .specly/check.json")
    check.set_defaults(run=command_check)
    fix = commands.add_parser("fix", help="skriv filene i Specly-format, og legg inn det neste eksport skriver etter «Bruk reglene»")
    fix.add_argument("--changed-from", metavar="REF", help="rett bare det endringene siden REF fører til")
    fix.add_argument("--dry-run", action="store_true", help="vis hva fix ville skrevet, og skriv ingenting")
    fix.add_argument("--apply-rules", action="store_true", help="skriv også det en kjøring av flaggreglene og kolonnesorteringsreglene i Specly ville gitt (nye flagg, ny kolonnerekkefølge), der filene avgjør det")
    fix.add_argument("--add-values", action="store_true", help="legg datatyper, tagger, statuser, tabelltyper og kildesystemer kontraktene bruker, men som mangler i registeret, til der (med uuid laget av navnet, slik Specly gjør)")
    fix.add_argument("--add-ids", action="store_true", help="gi tabeller og kolonner som er nye siden --changed-from, en id: den Specly selv ville laget (uuid v5 av prosjekt-id, kontraktens id, tabell- og kolonnenavn), så et nytt navn i Git senere blir en omdøping; en som hadde id i basen, får den tilbake. I et repo uten commits trengs ikke --changed-from: alt uten id får en")
    fix.add_argument("--ignore", metavar="KODE", action="append", default=[], help="ikke rett det funn med denne koden gjelder (som check --ignore)")
    fix.add_argument("--verbose", action="store_true", help="vis hele sporet når skriptet stopper på en feil")
    fix.set_defaults(run=command_fix, lineage_required=[])
    args = parser.parse_args()
    try:
        code = args.run(args)
        sys.stdout.flush()
        sys.exit(code)
    except BrokenPipeError:
        # Mottakeren lukket (check | head): ingen melding. Stdout pekes til /dev/null så Python ikke melder
        # feilen på nytt når den tømmer bufferet ved avslutning; exit 1, siden resultatet ikke kom fram.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
    except Stop as stop:
        print(stop, file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001 - en feil i skriptet skal ikke se ut som funn i repoet
        print(f"Sjekken stoppet på en feil i skriptet ({type(e).__name__}: {e}). Kjør med --verbose for hele sporet, og meld det til Specly.", file=sys.stderr)
        if getattr(args, "verbose", False):
            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
