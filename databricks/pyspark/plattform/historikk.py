"""Historikk (SCD2) fra leveransene.

For hver nøkkel ser vi på tidspunktene i rekkefølge. En ny versjon starter når radhashen (alle verdikolonnene)
er en annen enn ved forrige tidspunkt, eller når nøkkelen ikke fantes da. Med fullt uttrekk slutter en versjon
også ved første tidspunkt der nøkkelen mangler (raden er borte i kilden). Ellers er den åpen (9999-12-31).
Samme nøkkel to ganger i samme leveranse (den samme linjen to ganger i én fil) blir én rad.
"""
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from . import konstanter as k
from .felles import kolonne, nokkel_av, nokkel_med_tid, tidspunkt


def lag_historikk(rader: DataFrame, nokkel: list, tabell: str, fullt_uttrekk: bool = True,
                  tid: str = k.LASTET, tidspunkter: DataFrame = None) -> DataFrame:
    """Versjonene: én rad per nøkkel og versjon, med pk__, bk__, sys__gyldig_fra og sys__gyldig_til.

    rader       : én rad per nøkkel og tidspunkt (kolonnen `tid`); alle andre kolonner er verdier.
    nokkel      : BK-kolonnene (bk__ = hash av dem; pk__ = samme + gyldig fra).
    tidspunkter : alle tidspunktene (standard: de som finnes i `rader`). Sølv gir også tidspunktene der en
                  oppstrømsversjon sluttet, så en rad som forsvinner fra hovedtabellen lukkes.

    >>> lag_historikk(renset, nokkel=["VARENR"], tabell="brz__varius__vare", fullt_uttrekk=True)
    """
    verdier = [c for c in rader.columns if c != tid]
    o = rader.select("*", kolonne(tid).alias("_t"), nokkel_av(*nokkel).alias("_bk"), nokkel_av(*verdier).alias("_rad"))
    # Samme nøkkel flere ganger i samme leveranse: én rad (den med minst radhash, så valget er det samme hver gang).
    o = (o.select("*", F.row_number().over(Window.partitionBy("_bk", "_t").orderBy("_rad")).alias("_nr"))
          .where(F.col("_nr") == 1).drop("_nr"))
    tider = (tidspunkter if tidspunkter is not None else rader.select(kolonne(tid)))
    tider = tider.select(F.col(tider.columns[0]).alias("_t")).distinct()

    alle = Window.orderBy("_t")
    tidslinje = tider.select("_t", F.lag("_t").over(alle).alias("_forrige_t"), F.lead("_t").over(alle).alias("_neste_t"))

    per_nokkel = Window.partitionBy("_bk").orderBy("_t")
    naboer = o.join(tidslinje, "_t").select(
        "*",
        F.lag("_rad").over(per_nokkel).alias("_forrige_rad"),
        F.lag("_t").over(per_nokkel).alias("_forrige_t_nokkel"),
        F.lead("_t").over(per_nokkel).alias("_neste_t_nokkel"))

    # Med fullt uttrekk betyr en leveranse uten nøkkelen at raden var borte, så den starter en ny versjon når den kommer
    # tilbake. Med endringer betyr en leveranse uten nøkkelen bare «ingen endring».
    ny_versjon = F.col("_forrige_t_nokkel").isNull() | (F.col("_forrige_rad") != F.col("_rad"))
    if fullt_uttrekk:
        ny_versjon = ny_versjon | (F.col("_forrige_t_nokkel") != F.col("_forrige_t"))
    if fullt_uttrekk:
        borte = F.when(F.col("_neste_t").isNotNull() & (F.col("_neste_t_nokkel").isNull()
                       | (F.col("_neste_t_nokkel") != F.col("_neste_t"))), F.col("_neste_t"))
    else:
        borte = F.lit(None).cast("timestamp")
    merket = naboer.select("*", F.when(ny_versjon, 1).otherwise(0).alias("_start"), borte.alias("_borte"))

    hittil = per_nokkel.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    nummerert = merket.select("*", F.sum("_start").over(hittil).alias("_versjon"))
    med_slutt = nummerert.select("*", F.max("_borte").over(Window.partitionBy("_bk", "_versjon")).alias("_versjon_borte"))

    starter = med_slutt.where(F.col("_start") == 1)
    versjoner = starter.select(
        "*",
        F.col("_t").alias("_fra"),
        F.coalesce("_versjon_borte", F.lead("_t").over(per_nokkel), tidspunkt(k.APEN_SLUTT)).alias("_til"))

    return (versjoner
            .withColumn(k.PK.format(tabell=tabell), nokkel_med_tid(nokkel, "_fra"))
            .withColumn(k.BK.format(tabell=tabell), F.col("_bk"))
            .withColumn(k.FRA, F.col("_fra"))
            .withColumn(k.TIL, F.col("_til")))
