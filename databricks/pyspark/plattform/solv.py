"""Sølv: sett sammen oppstrømstabellene over tid (eller en union av dem), så Beregning og Radfilter. Historikken ligger i
historikk.py."""
from dataclasses import dataclass

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from . import konstanter as k
from .felles import gjelder_pa, kolonne, les_tabell, med_beregninger, tidspunkt


@dataclass(frozen=True)
class Kobling:
    """En annen oppstrømstabell, koblet til hovedtabellen med relasjonen i kontraktene.

    par    : kolonnepar (kolonne i denne tabellen, `hovedtabell.kolonne`), ett per kolonne i relasjonen.
    hvordan: "left" (standard): en rad i hovedtabellen uten treff er fortsatt med.

    >>> Kobling("brz__kassio__kvittering", par=[("storeId", "brz__kassio__kvitteringslinje.storeId"),
    ...                                        ("receiptNo", "brz__kassio__kvitteringslinje.receiptNo")])
    """
    tabell: str
    par: list
    hvordan: str = "left"


def tidspunktene(tabeller: list) -> DataFrame:
    """Alle tidspunktene der en av tabellene endret seg: hver versjons start, og slutt når den er lukket."""
    deler = []
    for t in tabeller:
        df = les_tabell(t)
        deler.append(df.select(F.col(k.FRA).alias("_t")))
        deler.append(df.where(F.col(k.TIL) < tidspunkt(k.APEN_SLUTT)).select(F.col(k.TIL).alias("_t")))
    ut = deler[0]
    for d in deler[1:]:
        ut = ut.union(d)
    return ut.distinct()


@dataclass(frozen=True)
class Gren:
    """Én gren i en union (feltet «Union av»): en hovedtabell, koblingene til den, og sølvkolonnene fra grenen.

    kolonner: sølvkolonnens navn → uttrykk over `tabell.kolonne` i grenens tabeller (tom() når grenen ikke har noen).

    >>> Gren("brz__nettora__ordrelinje", kolonner={"salgsnummer": kopi("brz__nettora__ordrelinje.order_id"), ...})
    """
    hovedtabell: str
    kolonner: dict
    koblinger: list = ()


def _rader(tider: DataFrame, hovedtabell: str, kolonner: dict, koblinger: list = (), radfilter: str = None) -> DataFrame:
    """For hvert tidspunkt: versjonene som gjaldt da i hovedtabellen og (LEFT) i koblingene, som sølvkolonner."""
    t = F.col("tider._t")
    hoved = les_tabell(hovedtabell)
    df = tider.alias("tider").join(hoved, gjelder_pa(t, kolonne(f"{hovedtabell}.{k.FRA}"), kolonne(f"{hovedtabell}.{k.TIL}")))
    for kb in koblinger:
        betingelse = gjelder_pa(t, kolonne(f"{kb.tabell}.{k.FRA}"), kolonne(f"{kb.tabell}.{k.TIL}"))
        for der, er_lik in kb.par:
            betingelse = betingelse & (kolonne(f"{kb.tabell}.{der}") == kolonne(er_lik))
        df = df.join(les_tabell(kb.tabell), betingelse, kb.hvordan)
    if radfilter:
        df = df.where(F.expr(radfilter))
    return df.select(t.alias("_tidspunkt"), *[uttrykk.alias(navn) for navn, uttrykk in kolonner.items()])


def sett_sammen_over_tid(hovedtabell: str, kolonner: dict, koblinger: list = (), beregninger: dict = None,
                         radfilter: str = None):
    """For hvert tidspunkt: versjonene som gjaldt da, i hovedtabellen og (LEFT) i koblingene, og sølvkolonnene.

    kolonner   : sølvkolonnens navn → uttrykk (kopi, nokkel_av …) over `tabell.kolonne` i oppstrømstabellene.
    beregninger: sølvkolonnens navn → (SQL fra feltet Beregning, datatype). Regnes etter `kolonner`, over sølvnavnene.
    radfilter  : feltet Radfilter, et SQL-predikat over oppstrømstabellenes kolonner.
    Gir (rader, tidspunkter) til lag_historikk.
    """
    tider = tidspunktene([hovedtabell] + [kb.tabell for kb in koblinger])
    rader = _rader(tider, hovedtabell, kolonner, koblinger, radfilter)
    return med_beregninger(rader, beregninger), tider


def sett_sammen_union(grener: list, beregninger: dict = None, radfilter: str = None):
    """Union (feltet «Union av»): radene fra hver gren over de samme tidspunktene, stablet, så
    Beregning over sølvnavnene. Tidspunktene er alle tidspunktene i alle grenene, så en rad fra én gren står ved hvert
    tidspunkt den gjelder, også når bare en annen gren endret seg da. Gir (rader, tidspunkter) til lag_historikk.

    >>> sett_sammen_union(grener=[Gren("brz__kassio__kvitteringslinje", ...), Gren("brz__nettora__ordrelinje", ...)],
    ...                   beregninger={"salgskanal": ("CASE WHEN sys__kildesystem = 'nettora' THEN 'Nett' ELSE 'Butikk' END", "string")})
    """
    tider = tidspunktene([t for g in grener for t in [g.hovedtabell] + [kb.tabell for kb in g.koblinger]])
    rader = None
    for g in grener:
        del_ = _rader(tider, g.hovedtabell, g.kolonner, g.koblinger, radfilter)
        rader = del_ if rader is None else rader.unionByName(del_)
    return med_beregninger(rader, beregninger), tider
