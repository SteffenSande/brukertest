"""Konstantene for hele plattformen. GENERERT av ./generer fra maler/pyspark/plattform.j2. Ikke rediger her."""

# Standardkolonnene (columnTemplates i specly/Config/table_types.json).
LASTET = "sys__lastet_tidspunkt"
KILDEFIL = "sys__kildefil"
UKJENTE = "sys__ukjente_kolonner"
KILDESYSTEM = "sys__kildesystem"
FRA = "sys__gyldig_fra"
TIL = "sys__gyldig_til"
PK = "pk__{tabell}"
BK = "bk__{tabell}"

# Gyldighetskolonnene i en SCD2-dimensjon i gull.
DIM_FRA = "gyldig_fra"
DIM_TIL = "gyldig_til"

# Åpen slutt på en versjon, og gyldig fra på spesialradene i en SCD2-dimensjon (SQL-literaler, brukes med F.expr).
APEN_SLUTT = "TIMESTAMP'9999-12-31 00:00:00'"
UKJENT_FRA = "TIMESTAMP'1900-01-01 00:00:00'"

# Tidspunktet i filnavnet …_ÅÅÅÅMMDDThhmm.<filtype>, som SQL-uttrykk over _metadata.
FILTIDSPUNKT = '''to_timestamp(regexp_extract(_metadata.file_name, '_([0-9]{8}T[0-9]{4})', 1), "yyyyMMdd'T'HHmm")'''

# De to spesialradene i hver gull-dimensjon: ukjent (nøkkelverdi uten treff) og mangler (tom nøkkel).
UKJENT_NOKKEL = -1
UKJENT_TEKST = "Ukjent"
MANGLER_NOKKEL = -2
MANGLER_TEKST = "Mangler"

# tom_til_null: disse verdiene blir NULL.
TOMME_VERDIER = ["", "N/A", "NA", "-"]

# Hashformelen.
TOM_NOKKELDEL = "∅"
NOKKEL_TIDSFORMAT = "yyyy-MM-dd HH:mm:ss"
IKKE_FUNNET = "∄"

# Datodimensjonen: pk__ er datoen som tallet ÅÅÅÅMMDD.
DATONOKKEL_FORMAT = "yyyyMMdd"
