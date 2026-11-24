"""Tags i Unity Catalog etter kontraktene (modul 8). Kjøres etter pipelinen, ikke i den.

Pipelinen kan ikke sette tags selv: dekoratoren har comment, schema og table_properties, men ingen tags. Derfor et eget
steg etter at pipelinen er ferdig: ./kjor (tools/sett_tags.py, gjennom SQL warehouse) og notebooks/kurs_generer_kjor og
kurs_til (med spark i notebooken).

Hvilke tags hver tabell og kolonne skal ha, står i tags_data.py, som ./generer lager fra kontraktene. Bare nøklene
kurset eier (EIDE_NOKLER, eier og klassifisering) røres: en eid nøkkel som ikke har verdi lenger, fjernes, og andre
tags får stå. Steget leser først hvilke tags som finnes (information_schema), og kjører bare det som må endres. Da kan
det kjøres så ofte du vil.

Ingen funksjon her nevner en tabell, en kolonne eller en tag ved navn.
"""

# Tabelltypen i information_schema.tables → ordet ALTER-setningen bruker. Pipelinen lager materialized views (og
# streaming tables for raw).
SQL_TYPE = {"MATERIALIZED_VIEW": "MATERIALIZED VIEW", "STREAMING_TABLE": "STREAMING TABLE", "VIEW": "VIEW"}
STANDARD_TYPE = "MATERIALIZED VIEW"


def sql_navn(*deler: str) -> str:
    """`katalog`.`skjema`.`tabell`: hvert ledd i backticks, en backtick i navnet doblet."""
    return ".".join("`" + d.replace("`", "``") + "`" for d in deler)


def sql_tekst(verdi) -> str:
    """En verdi som SQL-tekst: 'Salgsanalyse'. En ' i verdien dobles."""
    return "'" + str(verdi).replace("'", "''") + "'"


def onsket(tags: dict, eide: list) -> dict:
    """{(tabell, kolonne eller None): {nøkkel: verdi}} for de eide nøklene, fra TAGS i tags_data.py."""
    ut = {}
    for tabell, t in tags.items():
        ut[(tabell, None)] = {k: v for k, v in (t.get("tabell") or {}).items() if k in eide}
        for kolonne, kt in (t.get("kolonner") or {}).items():
            ut[(tabell, kolonne)] = {k: v for k, v in kt.items() if k in eide}
    return ut


def setninger(katalog: str, skjema: str, tags: dict, eide: list, finnes: dict | None = None,
               typer: dict | None = None) -> list:
    """SQL-setningene som gjør tags i Unity Catalog lik `tags`, for nøklene i `eide`.

    finnes: tags som står der nå, {(tabell, kolonne eller None): {nøkkel: verdi}}. Tom: ingenting står der.
    typer:  {tabell: tabelltypen i information_schema.tables}. Mangler en tabell: MATERIALIZED VIEW.
    Bare tabellene i `tags` røres. En tag som allerede har riktig verdi, gir ingen setning.

    >>> setninger("workspace", "toppfart", {"t": {"tabell": {"eier": "Salg"}, "kolonner": {}}}, ["eier"])
    ["ALTER MATERIALIZED VIEW `workspace`.`toppfart`.`t` SET TAGS ('eier' = 'Salg')"]
    """
    vil, har, typer = onsket(tags, eide), finnes or {}, typer or {}
    ut = []
    for (tabell, kolonne) in sorted(set(vil) | {n for n in har if n[0] in tags}, key=lambda n: (n[0], n[1] or "")):
        nye, gamle = vil.get((tabell, kolonne), {}), {k: v for k, v in har.get((tabell, kolonne), {}).items() if k in eide}
        sett = {k: v for k, v in nye.items() if gamle.get(k) != v}
        fjern = [k for k in eide if k in gamle and k not in nye]
        hvor = f"ALTER {SQL_TYPE.get(typer.get(tabell), STANDARD_TYPE)} {sql_navn(katalog, skjema, tabell)}"
        if kolonne is not None:
            hvor += f" ALTER COLUMN {sql_navn(kolonne)}"
        if sett:
            ut.append(f"{hvor} SET TAGS ({', '.join(f'{sql_tekst(k)} = {sql_tekst(v)}' for k, v in sett.items())})")
        if fjern:
            ut.append(f"{hvor} UNSET TAGS ({', '.join(sql_tekst(k) for k in fjern)})")
    return ut


def _sql(spark_eller_sql):
    """En funksjon spørring → rader (tupler), fra en Spark-økt eller en slik funksjon (SQL warehouse i ./kjor)."""
    if hasattr(spark_eller_sql, "sql"):
        return lambda q: [tuple(r) for r in spark_eller_sql.sql(q).collect()]
    return spark_eller_sql


def les_eksisterende(spark, katalog: str, skjema: str, eide: list) -> tuple:
    """(finnes, typer) for skjemaet, lest fra information_schema: de eide tagsene som står der nå, og tabelltypene.
    spark: en Spark-økt, eller en funksjon spørring → rader."""
    sql = _sql(spark)
    hvor = f"catalog_name = {sql_tekst(katalog)} AND schema_name = {sql_tekst(skjema)}"
    nokler = ", ".join(sql_tekst(k) for k in eide)
    finnes = {}
    for r in sql(f"SELECT table_name, tag_name, tag_value FROM {sql_navn(katalog)}.information_schema.table_tags "
                 f"WHERE {hvor} AND tag_name IN ({nokler})"):
        finnes.setdefault((r[0], None), {})[r[1]] = r[2]
    for r in sql(f"SELECT table_name, column_name, tag_name, tag_value FROM {sql_navn(katalog)}.information_schema.column_tags "
                 f"WHERE {hvor} AND tag_name IN ({nokler})"):
        finnes.setdefault((r[0], r[1]), {})[r[2]] = r[3]
    typer = {r[0]: r[1] for r in sql(
        f"SELECT table_name, table_type FROM {sql_navn(katalog)}.information_schema.tables "
        f"WHERE table_catalog = {sql_tekst(katalog)} AND table_schema = {sql_tekst(skjema)}")}
    return finnes, typer


def sett_tags(spark, katalog: str, skjema: str, tags: dict, eide: list) -> int:
    """Setter og fjerner tags i Unity Catalog etter kontraktene. Gir antall setninger som ble kjørt.
    spark: en Spark-økt (notebookene), eller en funksjon spørring → rader (./kjor, tools/sett_tags.py).

    >>> from plattform.tags_data import EIDE_NOKLER, TAGS
    >>> sett_tags(spark, "workspace", "toppfart", TAGS, EIDE_NOKLER)
    """
    sql = _sql(spark)
    finnes, typer = les_eksisterende(sql, katalog, skjema, eide)
    mangler = sorted(t for t in tags if t not in typer)
    if mangler:
        raise ValueError(f"Tabellene finnes ikke i {katalog}.{skjema}: {', '.join(mangler)}. Kjør pipelinen først.")
    alle = setninger(katalog, skjema, tags, eide, finnes, typer)
    for setning in alle:
        print(f"  {setning}")
        sql(setning)
    return len(alle)
