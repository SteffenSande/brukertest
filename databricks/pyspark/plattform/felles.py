"""Felles byggeklosser: kolonnelisten fra kontrakten, lesing av en annen tabell, nøkler (hash) og små uttrykk.

Ingen funksjon her nevner en tabell eller en kolonne ved navn. Alt tabellspesifikt kommer som argumenter fra den
genererte filen, som igjen kommer fra kontrakten.
"""
import re
from dataclasses import dataclass

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F

from . import konstanter as k


def spark() -> SparkSession:
    """Spark-økten pipelinen kjører i (i en importert modul finnes ikke den globale `spark`)."""
    return SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()


# ---------------------------------------------------------------- kolonnelisten fra kontrakten

@dataclass(frozen=True)
class Kolonne:
    """Én kolonne slik kontrakten beskriver den: navn, datatype og beskrivelse.

    >>> Kolonne("VARENR", "string", "Varenummeret uten ledende nuller.")
    """
    navn: str
    type: str
    beskrivelse: str = ""


def ddl(kolonner: list) -> str:
    """Tabellens skjema som DDL (til `schema=` i dekoratoren): typer og kommentarer fra kontrakten. En kolonne uten
    beskrivelse får ingen COMMENT, så Catalog Explorer ikke viser en tom kommentar."""
    def sql_tekst(s):
        return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

    def kommentar(c):
        return f" COMMENT {sql_tekst(c.beskrivelse)}" if (c.beskrivelse or "").strip() else ""
    return ",\n".join(f"`{c.navn}` {c.type.upper()}{kommentar(c)}" for c in kolonner)


def egenskaper(kontrakt: str, status: str) -> dict:
    """Tabellegenskapene alle tabellene får: hvilken kontrakt og hvilken status i Specly."""
    return {"specly.kontrakt": kontrakt, "specly.status": status}


def velg(df: DataFrame, kolonner: list) -> DataFrame:
    """Kontraktens kolonner, i kontraktens rekkefølge og med kontraktens datatyper. Hjelpekolonner faller bort."""
    return df.select(*[F.col(f"`{c.navn}`").cast(c.type).alias(c.navn) for c in kolonner])


# ---------------------------------------------------------------- lesing og uttrykk

def les_tabell(navn: str) -> DataFrame:
    """En annen tabell i samme pipeline, med tabellnavnet som alias (så `tabell.kolonne` virker i uttrykk)."""
    return spark().read.table(navn).alias(navn)


def kolonne(ref) -> Column:
    """`"tabell.kolonne"` eller `"kolonne"` som Spark-kolonne. En Column slippes gjennom uendret."""
    if isinstance(ref, Column):
        return ref
    deler = ref.rsplit(".", 1)
    return F.col(f"{deler[0]}.`{deler[1]}`") if len(deler) == 2 else F.col(f"`{ref}`")


def kopi(ref) -> Column:
    """Verdien fra oppstrømskolonnen, uendret. Over bronze har en kopi samme type som oppstrømmen (forhåndssjekken)."""
    return kolonne(ref)


def konstant(verdi) -> Column:
    """En fast verdi fra kontrakten (f.eks. kildesystemets navn)."""
    return F.lit(verdi)


def tom(som_type: str) -> Column:
    """Ingen verdi: en kolonne i en union som ikke har noen oppstrømskolonne i denne grenen."""
    return F.lit(None).cast(som_type)


def nokkel_sql(deler: list) -> str:
    """Nøkkelhashen (se nokkel_av) som SQL, over SQL-uttrykk. Samme formel, så hashen treffer bk__ i andre tabeller."""
    tom_del = k.TOM_NOKKELDEL.replace("'", "''")
    return "xxhash64(concat_ws('|', " + ", ".join(f"coalesce(cast(({d}) AS STRING), '{tom_del}')" for d in deler) + "))"


def _utvid_nokkel(uttrykk: str) -> str:
    """Bytter `nokkel(a, b)` i Beregning ut med nøkkelhashen av a og b (nokkel_sql). Strenger i uttrykket røres ikke."""
    ut, i = [], 0
    while True:
        m = re.search(r"(?<![A-Za-z0-9_.`])nokkel\s*\(", uttrykk[i:])
        if not m:
            return "".join(ut) + uttrykk[i:]
        start, j = i + m.start(), i + m.end()
        dybde, streng, deler, del_start = 1, False, [], j
        while dybde:
            if j >= len(uttrykk):
                raise ValueError(f"Beregning: nokkel( uten avsluttende parentes i «{uttrykk}».")
            tegn = uttrykk[j]
            if tegn == "'":
                streng = not streng
            elif not streng and tegn == "(":
                dybde += 1
            elif not streng and tegn == ")":
                dybde -= 1
            elif not streng and tegn == "," and dybde == 1:
                deler.append(uttrykk[del_start:j])
                del_start = j + 1
            j += 1
        deler.append(uttrykk[del_start:j - 1])
        ut.append(uttrykk[i:start] + nokkel_sql([_utvid_nokkel(d.strip()) for d in deler]))
        i = j


def beregn(uttrykk: str, som_type: str) -> Column:
    """Feltet Beregning: et SQL-uttrykk over kolonnenavnene i tabellen selv, castet til kolonnens type.
    Regnes ut etter de andre kolonnene, så det kan bruke dem. `nokkel(kolonne, …)` gir nøkkelhashen av kolonnene, den
    samme som bk__ i tabellen et fb__ peker på (for et fb__ som må regnes etter en annen Beregning).

    >>> beregn("antall * enhetspris_belop - rabatt_belop", som_type="decimal(10,2)")
    >>> beregn("nokkel(butikknummer)", som_type="bigint")
    """
    return F.expr(_utvid_nokkel(uttrykk)).cast(som_type)


def navn_i(uttrykk: str) -> set:
    """Ordene i et SQL-uttrykk som kan være kolonnenavn (strenger tatt ut)."""
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", re.sub(r"'[^']*'", " ", uttrykk or "")))


def med_beregninger(df: DataFrame, beregninger: dict) -> DataFrame:
    """Beregning for hver kolonne (navn → (SQL, type)), i en rekkefølge der en Beregning som bruker en annen
    beregnet kolonne, kommer etter den. En Beregning kan bruke kolonnens egen verdi (i en union: verdien fra grenene)."""
    igjen = dict(beregninger or {})
    while igjen:
        klare = [n for n, (sql, _) in igjen.items() if not (navn_i(sql) - {n}) & set(igjen)]
        if not klare:
            raise ValueError(f"Beregningene bruker hverandre i ring: {', '.join(igjen)}.")
        for n in klare:
            sql, typ = igjen.pop(n)
            df = df.withColumn(n, beregn(sql, typ))
    return df


def tidspunkt(sql_literal: str) -> Column:
    """En fast tidsverdi fra konstantene (f.eks. åpen slutt 9999-12-31)."""
    return F.expr(sql_literal)


# ---------------------------------------------------------------- nøkler

def nokkel_av(*refs, ikke_funnet_nar: Column = None) -> Column:
    """Nøkkelhashen: xxhash64(concat_ws('|', coalesce(cast(x AS string), '∅'), …)). Bare verdiene teller, så samme
    verdier i samme rekkefølge gir samme hash i alle tabeller (bk__, fb__ og fk__ treffer hverandre).

    ikke_funnet_nar: for et fb__ i sølv fra en annen oppstrømstabell enn hovedtabellen: når betingelsen er sann
                     (`ingen_treff`), blir nøkkelen `ikke_funnet()`, ikke hashen av verdiene.

    >>> nokkel_av("brz__kassio__kvitteringslinje.sku")     # fb__slv__produkt
    """
    h = F.xxhash64(F.concat_ws("|", *[F.coalesce(kolonne(r).cast("string"), F.lit(k.TOM_NOKKELDEL)) for r in refs]))
    return h if ikke_funnet_nar is None else F.when(ikke_funnet_nar, ikke_funnet()).otherwise(h)


def ikke_funnet() -> Column:
    """Nøkkelen «ikke funnet»: hashen av IKKE_FUNNET. Treffer aldri en ekte nøkkel og er ikke hash(∅), så gull gir -1."""
    return F.xxhash64(F.lit(k.IKKE_FUNNET))


def ingen_treff(hovedkolonne, koblet_kolonne) -> Column:
    """Sann når hovedtabellens koblingskolonne har en verdi, men koblingen ikke fant noen rad i den andre tabellen."""
    return kolonne(hovedkolonne).isNotNull() & kolonne(koblet_kolonne).isNull()


def tom_nokkel(deler: int = 1) -> Column:
    """hash(∅): hashen av en tom nøkkel med `deler` deler. En slik nøkkel treffer aldri, og fk__ blir -2 (mangler)."""
    return nokkel_av(*[F.lit(None) for _ in range(deler)])


def nokkel_med_tid(refs: list, gyldig_fra) -> Column:
    """pk__ i en tabell med historikk: nøkkelhashen av BK-kolonnene med gyldig fra til slutt."""
    deler = [F.coalesce(kolonne(r).cast("string"), F.lit(k.TOM_NOKKELDEL)) for r in refs]
    return F.xxhash64(F.concat_ws("|", *deler, F.date_format(kolonne(gyldig_fra), k.NOKKEL_TIDSFORMAT)))


def datonokkel(ref) -> Column:
    """pk__ i datodimensjonen: datoen som tallet ÅÅÅÅMMDD (2026-08-01 → 20260801)."""
    return F.date_format(kolonne(ref), k.DATONOKKEL_FORMAT).cast("bigint")


def gjelder_pa(tid: Column, fra: Column, til: Column) -> Column:
    """Sann når tidspunktet ligger i versjonens gyldighet: fra <= tid < til."""
    return (fra <= tid) & (tid < til)


def dagens_slutt(dato) -> Column:
    """Slutten av en dato: midnatt dagen etter."""
    return F.date_add(kolonne(dato), 1).cast("timestamp")


def gjelder_ved_dagens_slutt(dato, fra: Column, til: Column) -> Column:
    """Sann når versjonen gjaldt ved slutten av datoen: fra < dato + 1 dag <= til."""
    slutt = dagens_slutt(dato)
    return (fra < slutt) & (slutt <= til)
