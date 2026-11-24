"""Bronze: rensing og typer. Historikken ligger i historikk.py.

Rensingen er den faste listen i feltet Rensing, alltid i denne rekkefølgen:
trim, tom_til_null, fjern_ledende_nuller, store_bokstaver, ja_nei_til_boolsk. Så settes typen (cast_til).
"""
from dataclasses import dataclass, field

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from . import konstanter as k
from .felles import kolonne

# ---------------------------------------------------------------- de enkelte rensefunksjonene


def trim(x: Column) -> Column:
    """Fjerner mellomrom foran og bak. `' 4711 '` → `'4711'`"""
    return F.trim(x)


def tom_til_null(x: Column) -> Column:
    """`''`, `'N/A'`, `'NA'`, `'-'` → NULL."""
    return F.when(x.isin(*k.TOMME_VERDIER), F.lit(None)).otherwise(x)


def fjern_ledende_nuller(x: Column) -> Column:
    """`'004711'` → `'4711'` (`'0'` blir stående)."""
    return F.regexp_replace(x, "^0+(?=.)", "")


def store_bokstaver(x: Column) -> Column:
    """`'fri02'` → `'FRI02'`"""
    return F.upper(x)


def ja_nei_til_boolsk(x: Column) -> Column:
    """`'J'` → sann, `'N'` → usann, ellers NULL."""
    return F.when(F.upper(x) == "J", True).when(F.upper(x) == "N", False)


RENSING = {f.__name__: f for f in (trim, tom_til_null, fjern_ledende_nuller, store_bokstaver, ja_nei_til_boolsk)}
BOOLSK = {"ja_nei_til_boolsk"}


def rens(x: Column, rensing: list) -> Column:
    """Rensefunksjonene i `rensing`, i den faste rekkefølgen (ikke listens). Et ukjent navn stopper."""
    ukjent = set(rensing) - set(RENSING)
    if ukjent:
        raise ValueError(f"Ukjent rensing: {', '.join(sorted(ukjent))}. Kjente: {', '.join(RENSING)}.")
    for navn in RENSING:
        if navn in rensing:
            x = RENSING[navn](x)
    return x


# ---------------------------------------------------------------- typen, med kildesystemets format

@dataclass(frozen=True)
class Kildeformat:
    """Kildesystemets formatfelt (specly/Config/source_systems.json): hvordan tekst blir dato, tidspunkt og desimaltall.

    tidssone: sonen et tidspunkt er skrevet i når teksten selv ikke har sone. Tidspunktet gjøres om til UTC.

    >>> Kildeformat(dato="dd.MM.yyyy", desimaltegn=",")
    """
    dato: str = None
    tid: str = None
    desimaltegn: str = None
    tidssone: str = None


def cast_til(x: Column, til_type: str, kildeformat: Kildeformat) -> Column:
    """Den ene cast-funksjonen: tekst → kontraktens datatype, med kildesystemets format.
    En verdi som ikke lar seg gjøre om, blir NULL (try_), aldri en feil som stopper hele kjøringen.

    >>> cast_til(F.col("AAPNET_DT"), "date", Kildeformat(dato="dd.MM.yyyy"))          # '05.09.2026' → 2026-09-05
    >>> cast_til(F.col("UTPRIS"), "decimal(10,2)", Kildeformat(desimaltegn=","))      # '1299,00' → 1299.00
    >>> cast_til(F.col("soldAt"), "timestamp", Kildeformat(tid="yyyy-MM-dd'T'HH:mm:ssX", tidssone="UTC"))
    """
    t = til_type.lower()
    if t == "date":
        return F.to_date(F.try_to_timestamp(x, F.lit(kildeformat.dato))) if kildeformat.dato else x.try_cast("date")
    if t == "timestamp":
        ts = F.try_to_timestamp(x, F.lit(kildeformat.tid)) if kildeformat.tid else x.try_cast("timestamp")
        if kildeformat.tidssone and kildeformat.tidssone.upper() not in ("UTC", "Z", "ETC/UTC"):
            ts = F.to_utc_timestamp(ts, kildeformat.tidssone)
        return ts
    if t.startswith("decimal") and kildeformat.desimaltegn and kildeformat.desimaltegn != ".":
        return F.replace(x, F.lit(kildeformat.desimaltegn), F.lit(".")).try_cast(til_type)
    return x.try_cast(til_type)


# ---------------------------------------------------------------- én bronze-kolonne

@dataclass(frozen=True)
class Rens:
    """Én bronze-kolonne: navnet (samme som i raw), rensingen, og typen når den er en annen enn i raw.

    >>> Rens("VARENR", rensing=["trim", "fjern_ledende_nuller"])
    >>> Rens("UTPRIS", til_type="decimal(10,2)")
    """
    navn: str
    rensing: list = field(default_factory=list)
    til_type: str = None


def rens_og_cast(raw: DataFrame, kolonner: list, kildeformat: Kildeformat) -> DataFrame:
    """Hver raw-rad med rensede verdier i kontraktens typer, pluss leveransens tidspunkt og kildesystemet.

    >>> rens_og_cast(les_tabell("raw__varius__vare"), kolonner=[Rens("VARENR", rensing=["trim"])], kildeformat=Kildeformat())
    """
    ut = []
    for c in kolonner:
        x = rens(kolonne(c.navn), c.rensing)
        if c.til_type and not (c.til_type.lower() == "boolean" and BOOLSK & set(c.rensing)):
            x = cast_til(x, c.til_type, kildeformat)
        ut.append(x.alias(c.navn))
    return raw.select(*ut, kolonne(k.LASTET).alias(k.LASTET), kolonne(k.KILDESYSTEM).alias(k.KILDESYSTEM))
