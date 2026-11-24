"""Gull: dimensjoner (SCD1/SCD2 + spesialradene -1 og -2) og fakta (oppslag av fk__, Beregning)."""
from dataclasses import dataclass

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from . import konstanter as k
from .felles import (datonokkel, gjelder_pa, gjelder_ved_dagens_slutt, kolonne, les_tabell, med_beregninger,
                     nokkel_av, nokkel_med_tid, spark, tidspunkt, tom_nokkel, velg)

# ---------------------------------------------------------------- dimensjon


@dataclass(frozen=True)
class Oppslag:
    """En annen sølvtabell som dimensjonen henter kolonner fra, via hovedtabellens fb__-kolonne.

    nokkeldeler: antall BK-kolonner i den andre tabellen (for hash(∅): en tom nøkkel treffer aldri).

    >>> Oppslag("slv__produktgruppe", via="fb__slv__produktgruppe")
    """
    tabell: str
    via: str
    nokkeldeler: int = 1


def _med_siste(tabell: str) -> DataFrame:
    """Sølvversjonene med et merke på siste versjon per nøkkel."""
    nyest = Window.partitionBy(k.BK.format(tabell=tabell)).orderBy(F.col(k.FRA).desc())
    return les_tabell(tabell).select("*", (F.row_number().over(nyest) == 1).alias("_siste")).alias(tabell)


def lag_dimensjon(hovedtabell: str, kolonner: dict, nokkel: list, tabell: str, historikk: str,
                  oppslag: list = (), datonokkel_pa: bool = False) -> DataFrame:
    """Dimensjonen fra sølv (uten spesialradene; se med_spesialrader).

    historikk "SCD1": siste versjon per nøkkel; pk__ = bk__ = hash(BK). Oppslag tar siste versjon.
    historikk "SCD2": alle versjoner; gyldig_fra/til = sølvens sys__gyldig_fra/til; pk__ = hash(BK + gyldig_fra).
                      Oppslag tar versjonen som gjaldt da hovedtabellens versjon startet.
    datonokkel_pa   : datodimensjonen (én BK-kolonne av typen date): pk__ er datoen som tallet ÅÅÅÅMMDD.

    >>> lag_dimensjon(hovedtabell="slv__produkt", historikk="SCD1", nokkel=["varenummer"], tabell="gld__d__produkt",
    ...               oppslag=[Oppslag("slv__produktgruppe", via="fb__slv__produktgruppe")],
    ...               kolonner={"varenummer": kopi("slv__produkt.varenummer"), ...})
    """
    scd2 = historikk == "SCD2"
    df = _med_siste(hovedtabell)
    for o in oppslag:
        andre = _med_siste(o.tabell)
        betingelse = ((kolonne(f"{o.tabell}.{k.BK.format(tabell=o.tabell)}") == kolonne(f"{hovedtabell}.{o.via}"))
                      & (kolonne(f"{hovedtabell}.{o.via}") != tom_nokkel(o.nokkeldeler)))
        if scd2:
            betingelse = betingelse & gjelder_pa(kolonne(f"{hovedtabell}.{k.FRA}"),
                                                 kolonne(f"{o.tabell}.{k.FRA}"), kolonne(f"{o.tabell}.{k.TIL}"))
        else:
            betingelse = betingelse & kolonne(f"{o.tabell}._siste")
        df = df.join(andre, betingelse, "left")
    if not scd2:
        df = df.where(kolonne(f"{hovedtabell}._siste"))

    uttrykk = dict(kolonner)
    bk = [uttrykk[n] for n in nokkel]
    if datonokkel_pa:
        pk = datonokkel(bk[0])
    elif scd2:
        pk = nokkel_med_tid(bk, uttrykk[k.DIM_FRA])
    else:
        pk = nokkel_av(*bk)
    return df.select(pk.alias(k.PK.format(tabell=tabell)), nokkel_av(*bk).alias(k.BK.format(tabell=tabell)),
                     *[u.alias(n) for n, u in uttrykk.items()])


def spesialrad_verdi(c, tabell: str, nokkel: int, tekst: str):
    """Verdien en kolonne får i en spesialrad: pk__/bk__ = nøkkelen (-1 eller -2), tekst «Ukjent»/«Mangler»,
    gyldighet UKJENT_FRA til 9999, systemkolonner og alt annet tomt."""
    if c.navn in (k.PK.format(tabell=tabell), k.BK.format(tabell=tabell)):
        return F.lit(nokkel).cast(c.type)
    if c.navn == k.DIM_FRA:
        return tidspunkt(k.UKJENT_FRA)
    if c.navn == k.DIM_TIL:
        return tidspunkt(k.APEN_SLUTT)
    if c.type.lower() == "string" and not c.navn.startswith("sys__"):
        return F.lit(tekst)
    return F.lit(None).cast(c.type)


def med_spesialrader(dimensjon: DataFrame, kolonner: list, tabell: str) -> DataFrame:
    """Dimensjonen i kontraktens rekkefølge, pluss de to spesialradene faktaen peker på:
    ukjent-raden (pk__ = bk__ = -1, «Ukjent») og mangler-raden (-2, «Mangler»)."""
    df = velg(dimensjon, kolonner)
    for nokkel, tekst in ((k.UKJENT_NOKKEL, k.UKJENT_TEKST), (k.MANGLER_NOKKEL, k.MANGLER_TEKST)):
        df = df.unionByName(spark().range(1).select(*[spesialrad_verdi(c, tabell, nokkel, tekst).alias(c.navn) for c in kolonner]))
    return df


# ---------------------------------------------------------------- fakta

def gjeldende_versjoner(tabell: str, radfilter: str = None) -> DataFrame:
    """De gjeldende versjonene i en sølvtabell (fakta bygges fra dem), med Radfilteret fra kontrakten."""
    df = les_tabell(tabell).where(F.col(k.TIL) == tidspunkt(k.APEN_SLUTT))
    return df.where(F.expr(radfilter)) if radfilter else df


def oyeblikksbilde(tabell: str, kalender: str, dag: str, radfilter: str = None) -> DataFrame:
    """Periodisk øyeblikksbilde (feltet Faktatype): for hver dag i kalenderen, versjonene i sølvtabellen som gjaldt ved
    slutten av dagen, fra dagen for første til dagen for siste leveranse. En dag uten ny leveranse (en søndag
    uten telling) får versjonen fra dagen før. Gir radene med både `tabell.kolonne` og `kalender.kolonne`.

    dag: datokolonnen i kalenderen, som `kalender.kolonne`.

    >>> oyeblikksbilde("slv__lagerbeholdning", kalender="slv__dato", dag="slv__dato.dato")
    """
    versjoner = les_tabell(tabell)
    if radfilter:
        versjoner = versjoner.where(F.expr(radfilter))
    grenser = versjoner.agg(F.to_date(F.min(k.FRA)).alias("_forste_dag"), F.to_date(F.max(k.FRA)).alias("_siste_dag"))
    dager = (les_tabell(kalender).crossJoin(grenser)
             .where(kolonne(dag).between(F.col("_forste_dag"), F.col("_siste_dag"))))
    return dager.join(versjoner, gjelder_ved_dagens_slutt(dag, kolonne(f"{tabell}.{k.FRA}"), kolonne(f"{tabell}.{k.TIL}")))


def lag_kolonner(df: DataFrame, kolonner: dict, beregninger: dict = None) -> DataFrame:
    """Faktaens kolonner: navn → uttrykk (kopi, nokkel_av …), så Beregning (navn → (SQL, type)) over faktaens navn."""
    return med_beregninger(df.select(*[u.alias(n) for n, u in kolonner.items()]), beregninger)


def sla_opp_nokkel(fakta: DataFrame, kolonne_navn: str, dimensjon: str, datoeffektiv_pa: str = None,
                   nokkeldeler: int = 1) -> DataFrame:
    """fk__: bytter koblingsnøkkelen (hashen av nøkkelverdiene, = dimensjonens bk__) ut med dimensjonens pk__.
    Tom nøkkel (hash(∅)) → -2 (mangler-raden); nøkkel uten treff → -1 (ukjent-raden). En faktarad forsvinner aldri.

    datoeffektiv_pa: mot en SCD2-dimensjon, datoen som velger versjonen: den som gjaldt ved slutten av dagen.

    >>> sla_opp_nokkel(fakta, "fk__gld__d__produkt", dimensjon="gld__d__produkt")
    """
    d = f"_dim_{kolonne_navn}"
    dim = spark().read.table(dimensjon).alias(d)
    f = fakta.alias("_fakta")
    betingelse = ((kolonne(f"{d}.{k.BK.format(tabell=dimensjon)}") == kolonne(f"_fakta.{kolonne_navn}"))
                  & (kolonne(f"_fakta.{kolonne_navn}") != tom_nokkel(nokkeldeler)))
    if datoeffektiv_pa:
        betingelse = betingelse & gjelder_ved_dagens_slutt(f"_fakta.{datoeffektiv_pa}", kolonne(f"{d}.{k.DIM_FRA}"),
                                                           kolonne(f"{d}.{k.DIM_TIL}"))
    funnet = (F.when(kolonne(f"_fakta.{kolonne_navn}") == tom_nokkel(nokkeldeler), F.lit(k.MANGLER_NOKKEL))
              .otherwise(F.coalesce(kolonne(f"{d}.{k.PK.format(tabell=dimensjon)}"), F.lit(k.UKJENT_NOKKEL))))
    return f.join(dim, betingelse, "left").select(
        *[kolonne(f"_fakta.{c}") if c != kolonne_navn else funnet.cast("bigint").alias(c) for c in fakta.columns])


def med_primaernokkel(fakta: DataFrame, nokkel: list, tabell: str) -> DataFrame:
    """pk__ = hash av BK-kolonnene."""
    return fakta.withColumn(k.PK.format(tabell=tabell), nokkel_av(*nokkel))
