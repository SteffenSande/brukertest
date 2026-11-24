"""Raw: les nye filer fra landing. Bare filformatet endres; systemkolonnene legges til."""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from . import konstanter as k
from .felles import ddl, spark, velg


def landingssone() -> str:
    """Mappen med landingsfilene. Kommer fra pipelinens konfigurasjon (databricks.yml), aldri fra koden:
    `plattform.landing`, ellers /Volumes/<plattform.katalog>/<plattform.skjema>/<plattform.volum>
    (standard workspace, toppfart, landing)."""
    conf = spark().conf
    sti = conf.get("plattform.landing", None)
    if sti:
        return sti.rstrip("/")
    return "/Volumes/{}/{}/{}".format(conf.get("plattform.katalog", "workspace"), conf.get("plattform.skjema", "toppfart"),
                                      conf.get("plattform.volum", "landing"))


def les_landingsfiler(filer: str, filformat: str, kolonner: list, kildesystem: str, skilletegn: str = None) -> DataFrame:
    """Streaming-lesing (Auto Loader) av landingsfilene til én kildetabell. Hver fil leses én gang.

    - Lese-skjemaet er kontraktens kolonner minus standardkolonnene (CSV: tekst).
    - Felt i filen som kontrakten ikke kjenner, havner som JSON i sys__ukjente_kolonner (rescued data).
    - sys__lastet_tidspunkt = tidspunktet i filnavnet; sys__kildefil = hele stien; sys__kildesystem = kildesystemet.

    >>> les_landingsfiler("kassio/kvittering/kvittering_*.csv", filformat="csv", skilletegn=",", kildesystem="kassio", kolonner=KOLONNER)
    """
    standard = {k.LASTET, k.KILDEFIL, k.UKJENTE, k.KILDESYSTEM}
    fra_filen = [c for c in kolonner if c.navn not in standard]
    leser = (spark().readStream.format("cloudFiles")
             .option("cloudFiles.format", filformat)
             .option("rescuedDataColumn", k.UKJENTE))
    if filformat == "csv":
        leser = leser.option("header", "true").option("sep", skilletegn)
    df = leser.schema(ddl(fra_filen)).load(f"{landingssone()}/{filer}")
    return velg(med_systemkolonner(df, kildesystem), kolonner)


def med_systemkolonner(df: DataFrame, kildesystem: str) -> DataFrame:
    """Systemkolonnene raw legger til hver rad: når filen kom, hvilken fil, og hvilket kildesystem."""
    return (df.withColumn(k.LASTET, F.expr(k.FILTIDSPUNKT))
              .withColumn(k.KILDEFIL, F.col("_metadata.file_path"))
              .withColumn(k.KILDESYSTEM, F.lit(kildesystem)))
