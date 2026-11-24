"""Tags i Unity Catalog per tabell. GENERERT av ./generer (maler/pyspark/tags.py.j2) fra kontraktene. Ikke rediger.

plattform/tags.py setter dem etter at pipelinen er ferdig (modul 8).
"""

# Nøklene kurset eier. Står en nøkkel her, men ikke på tabellen eller kolonnen, fjernes taggen.
EIDE_NOKLER = ["eier", "klassifisering"]

TAGS = {
    "brz__kalender__dag": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__kassio__kvittering": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__kassio__kvitteringslinje": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__lagra__beholdning": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__lojal__medlem": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__nettora__ordrelinje": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__varius__aktor": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__varius__vare": {
        "tabell": {},
        "kolonner": {},
    },
    "brz__varius__varegruppe": {
        "tabell": {},
        "kolonner": {},
    },
    "gld__d__butikk": {
        "tabell": {"eier": "Salgsanalyse", "klassifisering": "intern"},
        "kolonner": {
            "pk__gld__d__butikk": {"klassifisering": "intern"},
            "bk__gld__d__butikk": {"klassifisering": "intern"},
            "butikknummer": {"klassifisering": "intern"},
            "apnet_dato": {"klassifisering": "offentlig"},
            "butikknavn": {"klassifisering": "offentlig"},
            "kommune": {"klassifisering": "offentlig"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "gld__d__dato": {
        "tabell": {"eier": "Dataplattform", "klassifisering": "intern"},
        "kolonner": {
            "pk__gld__d__dato": {"klassifisering": "intern"},
            "bk__gld__d__dato": {"klassifisering": "intern"},
            "dato": {"klassifisering": "offentlig"},
            "ar": {"klassifisering": "offentlig"},
            "er_helligdag": {"klassifisering": "offentlig"},
            "kvartal": {"klassifisering": "offentlig"},
            "maned": {"klassifisering": "offentlig"},
            "uke": {"klassifisering": "offentlig"},
            "ukedag": {"klassifisering": "offentlig"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "gld__d__kunde": {
        "tabell": {"eier": "Kundeklubben", "klassifisering": "fortrolig"},
        "kolonner": {
            "pk__gld__d__kunde": {"klassifisering": "intern"},
            "bk__gld__d__kunde": {"klassifisering": "fortrolig"},
            "medlemsnummer": {"klassifisering": "fortrolig"},
            "gyldig_fra": {"klassifisering": "intern"},
            "gyldig_til": {"klassifisering": "intern"},
            "innmeldt_dato": {"klassifisering": "intern"},
            "medlemsniva": {"klassifisering": "intern"},
            "postnummer": {"klassifisering": "fortrolig"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "gld__d__produkt": {
        "tabell": {"eier": "Sortiment", "klassifisering": "intern"},
        "kolonner": {
            "pk__gld__d__produkt": {"klassifisering": "intern"},
            "bk__gld__d__produkt": {"klassifisering": "intern"},
            "varenummer": {"klassifisering": "intern"},
            "er_aktiv": {"klassifisering": "intern"},
            "hovedgruppe": {"klassifisering": "offentlig"},
            "leverandornavn": {"klassifisering": "intern"},
            "merke": {"klassifisering": "offentlig"},
            "produktgruppekode": {"klassifisering": "offentlig"},
            "produktgruppenavn": {"klassifisering": "offentlig"},
            "produktnavn": {"klassifisering": "offentlig"},
            "utpris_belop": {"klassifisering": "offentlig"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "gld__f__lagerbeholdning": {
        "tabell": {"eier": "Sortiment", "klassifisering": "intern"},
        "kolonner": {
            "pk__gld__f__lagerbeholdning": {"klassifisering": "intern"},
            "fk__gld__d__butikk": {"klassifisering": "intern"},
            "fk__gld__d__dato": {"klassifisering": "intern"},
            "fk__gld__d__produkt": {"klassifisering": "intern"},
            "butikknummer": {"klassifisering": "intern"},
            "dato": {"klassifisering": "intern"},
            "varenummer": {"klassifisering": "intern"},
            "antall_i_bestilling": {"klassifisering": "intern"},
            "antall_pa_lager": {"klassifisering": "intern"},
            "telling_dato": {"klassifisering": "intern"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "gld__f__salg": {
        "tabell": {"eier": "Salgsanalyse", "klassifisering": "fortrolig"},
        "kolonner": {
            "pk__gld__f__salg": {"klassifisering": "intern"},
            "fk__gld__d__butikk": {"klassifisering": "intern"},
            "fk__gld__d__dato": {"klassifisering": "intern"},
            "fk__gld__d__kunde": {"klassifisering": "intern"},
            "fk__gld__d__produkt": {"klassifisering": "intern"},
            "butikknummer": {"klassifisering": "intern"},
            "linjenummer": {"klassifisering": "intern"},
            "salgsnummer": {"klassifisering": "intern"},
            "antall": {"klassifisering": "fortrolig"},
            "belop": {"klassifisering": "fortrolig"},
            "enhetspris_belop": {"klassifisering": "fortrolig"},
            "rabatt_belop": {"klassifisering": "fortrolig"},
            "salg_dato": {"klassifisering": "intern"},
            "sys__kildesystem": {"klassifisering": "intern"},
        },
    },
    "raw__kalender__dag": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__kassio__kvittering": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__kassio__kvitteringslinje": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__lagra__beholdning": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__lojal__medlem": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__nettora__ordrelinje": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__varius__aktor": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__varius__vare": {
        "tabell": {},
        "kolonner": {},
    },
    "raw__varius__varegruppe": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__butikk": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__dato": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__kunde": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__lagerbeholdning": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__leverandor": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__produkt": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__produktgruppe": {
        "tabell": {},
        "kolonner": {},
    },
    "slv__salgslinje": {
        "tabell": {},
        "kolonner": {},
    },
}
