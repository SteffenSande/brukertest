# /// script
# requires-python = ">=3.11"
# dependencies = ["pyarrow==26.0.1"]
# ///
"""Deterministisk datagenerator og fasit for Specly-kurset (Toppfart Sport AS, oppdiktet).

Kjør fra repo-roten:
    uv run tools/lag_data.py              # skriver data/landing/..., fasit/fasit.json og docs/fasit.md
    uv run tools/lag_data.py --rot DIR    # skriver alt under DIR (brukes av selvtesten)

Skriver:
    data/landing/<kilde>/<tabell>/<tabell>_ÅÅÅÅMMDDThhmm.<csv|json|parquet>   (design.md kap. 3)
    fasit/fasit.json   maskinlesbar svarnøkkel per modul
    docs/fasit.md      kort norsk oversikt over de viktigste tallene (generert, ikke rediger for hånd)

Prinsipp: generatoren lager først sannheten (rene verdier: heltall, Decimal, datoer, UTC-tidspunkt) og
simulerer salg og lager dag for dag. Landingsfilene skrives fra sannheten med kildenes skrivemåter (ledende
nuller, desimalkomma, dd.MM.yyyy, UTC). Fasiten regnes direkte fra sannheten i Python. Den leser aldri
filene og etterligner ikke pipelinen.

Hendelsene H1-H17 (design.md kap. 6) plantes på datoene og i kildene designet sier. Alt annet er stabilt
mellom uttrekk: en verdi som ikke skal endres, skrives likt i hvert uttrekk.

Bare standardbiblioteket, unntatt Parquet-skrivingen (pyarrow, låst versjon for byte-like filer).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

SEED = 20261122
OSLO = ZoneInfo("Europe/Oslo")
UTC = timezone.utc

FRA = date(2026, 8, 1)
TIL = date(2026, 10, 31)
DAGER = [FRA + timedelta(days=i) for i in range((TIL - FRA).days + 1)]
UKEDAGER = ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"]
KRONE = Decimal("0.01")


def kr(x) -> Decimal:
    return Decimal(x).quantize(KRONE, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Tilfeldighet: bare random() brukes, så tallrekken er lik på alle Python-versjoner.
# Hvert område har sin egen strøm, slik at en endring ett sted ikke flytter alt annet.
# ---------------------------------------------------------------------------
class Trekk:
    def __init__(self, navn: str):
        self.r = random.Random(f"{SEED}:{navn}")

    def tall(self) -> float:
        return self.r.random()

    def heltall(self, lo: int, hi: int) -> int:  # lo..hi inklusive
        return lo + int(self.r.random() * (hi - lo + 1))

    def velg(self, liste):
        return liste[int(self.r.random() * len(liste))]

    def vektet(self, liste, vekter):
        tot = sum(vekter)
        x = self.r.random() * tot
        for el, v in zip(liste, vekter):
            x -= v
            if x < 0:
                return el
        return liste[-1]

    def stokk(self, liste):
        liste = list(liste)
        for i in range(len(liste) - 1, 0, -1):
            j = int(self.r.random() * (i + 1))
            liste[i], liste[j] = liste[j], liste[i]
        return liste


# ---------------------------------------------------------------------------
# Leveranser og filnavn (design.md 3.1)
# ---------------------------------------------------------------------------
TABELLER = {  # nøkkel -> (kilde, tabell, filtype)
    "varius__vare": ("varius", "vare", "csv"),
    "varius__varegruppe": ("varius", "varegruppe", "csv"),
    "varius__aktor": ("varius", "aktor", "csv"),
    "kassio__kvittering": ("kassio", "kvittering", "csv"),
    "kassio__kvitteringslinje": ("kassio", "kvitteringslinje", "csv"),
    "nettora__ordrelinje": ("nettora", "ordrelinje", "json"),
    "lojal__medlem": ("lojal", "medlem", "json"),
    "lagra__beholdning": ("lagra", "beholdning", "parquet"),
    "kalender__dag": ("kalender", "dag", "csv"),
}
KOLONNER = {
    "varius__vare": ["VARENR", "VARETEKST", "VGRP", "LEVNR", "MERKE", "UTPRIS", "STATUS"],
    "varius__varegruppe": ["VGRP", "VGRP_TEKST", "HOVEDGRP"],
    "varius__aktor": ["AKTNR", "AKTTYPE", "NAVN", "KOMMUNE", "AAPNET_DT", "ORGNR"],
    "kassio__kvittering": ["storeId", "receiptNo", "soldAt", "memberNo", "paymentType"],
    "kassio__kvitteringslinje": ["storeId", "receiptNo", "lineNo", "sku", "qty", "unitPrice", "discount"],
    "nettora__ordrelinje": ["order_id", "line_no", "customer_id", "ordered_at", "product_code", "quantity", "price"],
    "lojal__medlem": ["memberId", "firstName", "lastName", "postalCode", "tier", "joinedDate"],
    "lagra__beholdning": ["whs_store", "item_no", "count_date", "on_hand", "on_order"],
    "kalender__dag": ["DATO", "UKEDAG", "UKE", "MND", "KVARTAL", "AAR", "HELLIGDAG"],
}
SKILLETEGN = {"varius": ";", "kassio": ",", "kalender": ","}

VARE_UTTREKK = [datetime(2026, 8, 1, 5, 0), datetime(2026, 9, 1, 5, 0), datetime(2026, 10, 1, 5, 0)]
KALENDER_FIL = datetime(2026, 7, 31, 6, 0)
# H12: filene for 12. september kommer 14. september. Kl. 06 den dagen er allerede tatt av filen for
# 13. september, så den forsinkede filen får sitt eget tidspunkt samme formiddag.
SEN_DAG = date(2026, 9, 12)
SEN_ANKOMST = datetime(2026, 9, 14, 9, 30)
H10_FRA = date(2026, 10, 1)  # campaignCode i filene med salg fra og med denne datoen


def kasse_ankomst(d: date) -> datetime:
    if d == SEN_DAG:
        return SEN_ANKOMST
    return datetime.combine(d + timedelta(days=1), time(6, 0))


def nett_ankomst(d: date) -> datetime:
    return datetime.combine(d + timedelta(days=1), time(6, 0))


def klubb_uttrekk(d: date) -> datetime:
    return datetime.combine(d, time(4, 0))


def lager_telling(d: date) -> datetime:
    return datetime.combine(d, time(23, 0))


def er_tellingsdag(d: date) -> bool:  # H16: lagersystemet teller mandag til lørdag
    return d.weekday() != 6


def filsti(nokkel: str, ankomst: datetime) -> str:
    kilde, tabell, ext = TABELLER[nokkel]
    return f"data/landing/{kilde}/{tabell}/{tabell}_{ankomst.strftime('%Y%m%dT%H%M')}.{ext}"


# ---------------------------------------------------------------------------
# SANNHETEN: aktører, varegrupper, varer
# ---------------------------------------------------------------------------
BUTIKKER = [  # aktnr, navn, kommune, åpnet
    (101, "Toppfart Majorstuen", "Oslo", date(2012, 4, 14)),
    (102, "Toppfart Bergen sentrum", "Bergen", date(2014, 9, 6)),
    (103, "Toppfart Solsiden", "Trondheim", date(2015, 3, 21)),
    (104, "Toppfart Stavanger", "Stavanger", date(2017, 10, 7)),
    (105, "Toppfart Tromsø", "Tromsø", date(2019, 11, 2)),
    (106, "Toppfart Lillehammer", "Lillehammer", date(2026, 9, 5)),  # H5
    (107, "Toppfart nettbutikk", "", date(2018, 2, 1)),
]
NETTBUTIKK = 107
FYSISKE = [101, 102, 103, 104, 105, 106]
LILLEHAMMER = 106
LILLEHAMMER_APNER = date(2026, 9, 5)
LILLEHAMMER_I_VARESYSTEM = VARE_UTTREKK[1]  # H5: med fra uttrekket 1. september
BUTIKKVEKT = {101: 1.35, 102: 1.15, 103: 1.0, 104: 1.0, 105: 0.75, 106: 0.85}

LEVERANDORER = [  # aktnr, navn, kommune, orgnr, merke
    (501, "Fjellvind Utstyr AS", "Oslo", "910000015", "Fjellvind"),
    (502, "Nordtind Sport AS", "Bergen", "910000023", "Nordtind"),
    (503, "Løypefart AS", "Lillehammer", "910000031", "Løypefart"),
    (504, "Kystløp AS", "Stavanger", "910000058", "Kystløp"),
    (505, "Trå Sykkel AS", "Trondheim", "910000066", "Trå"),
    (506, "Polarlys Tekstil AS", "Tromsø", "910000074", "Polarlys"),
    (507, "Skarfjell Ski AS", "", "910000082", "Skarfjell"),
    (508, "Vidda Friluft AS", "Gjøvik", "910000090", "Vidda"),
    (509, "Tindrift AS", "", "910000104", "Tindrift"),
    (510, "Velonord Import AS", "Drammen", "910000112", "Velonord"),
]
MERKE = {a: m for a, _, _, _, m in LEVERANDORER}

VAREGRUPPER = [  # kode, tekst, hovedgruppe, leverandører
    ("SKI01", "Langrennsski", "Ski", [507, 503]),
    ("SKI02", "Skisko og bindinger", "Ski", [503, 507]),
    ("SKI03", "Skismøring og tilbehør", "Ski", [503, 509]),
    ("LOP01", "Løpesko", "Løping", [504, 509]),
    ("LOP02", "Løpeklær", "Løping", [506, 504]),
    ("LOP03", "Løpetilbehør", "Løping", [504, 506]),
    ("FRI01", "Telt og soveposer", "Friluftsliv", [508, 501]),
    ("FRI02", "Staver og stavtilbehør", "Friluftsliv", [502, 501]),
    ("FRI03", "Sekker", "Friluftsliv", [501, 508]),
    ("SYK01", "Sykler", "Sykkel", [505, 510]),
    ("SYK02", "Sykkelklær", "Sykkel", [506, 505]),
    ("SYK03", "Sykkeltilbehør", "Sykkel", [510, 505]),
]
HOVEDGRUPPE = {k: h for k, _, h, _ in VAREGRUPPER}
SESONG = {  # salgsvekt per hovedgruppe i august og oktober (lineært mellom)
    "Ski": (0.25, 1.4), "Løping": (1.2, 0.9), "Friluftsliv": (1.2, 0.8), "Sykkel": (1.3, 0.45),
}

VARER_PER_GRUPPE = {  # (varetekst, utpris i hele kroner)
    "SKI01": [("Klassiskski skin 197 cm", 3299), ("Klassiskski skin 202 cm", 3299), ("Klassiskski voks 202 cm", 2999),
              ("Skøyteski 186 cm", 3999), ("Skøyteski 192 cm", 3999), ("Turski fjell 185 cm", 2799),
              ("Turski fjell 195 cm", 2799), ("Juniorski klassisk 150 cm", 1299), ("Juniorski klassisk 170 cm", 1399),
              ("Fjellski stålkant 180 cm", 3499), ("Rulleski klassisk", 2499), ("Rulleski skøyte", 2699),
              ("Barneski 120 cm", 799)],
    "SKI02": [("Skisko klassisk", 1999), ("Skisko skøyte", 2299), ("Skisko kombi", 1799), ("Fjellsko telemark", 3299),
              ("Juniorsko kombi", 899), ("Binding klassisk", 799), ("Binding skøyte", 849), ("Binding fjell", 1499),
              ("Binding junior", 449), ("Skisko tur dame", 1599), ("Skisko tur herre", 1599), ("Skoposer termo", 349),
              ("Skisko racing", 3999)],
    "SKI03": [("Glider rød", 199), ("Glider blå", 199), ("Festevoks blå", 129), ("Festevoks lilla", 129),
              ("Klister universal", 149), ("Smørebukk sammenleggbar", 1499), ("Sikle plast", 79), ("Børste nylon", 249),
              ("Skipose dobbel", 699), ("Skifeller tur 120 mm", 1299), ("Smørejern", 899),
              ("Skistropper 2-pk", 59)],
    "LOP01": [("Løpesko vei dame", 1699), ("Løpesko vei herre", 1699), ("Terrengløpesko dame", 1899),
              ("Terrengløpesko herre", 1899), ("Konkurransesko karbon", 2999), ("Løpesko vinter dame", 1999),
              ("Løpesko vinter herre", 1999), ("Løpesko junior", 899), ("Treningssko allround", 1299),
              ("Piggsko friidrett", 1199), ("Løpesko stabil dame", 1799), ("Løpesko stabil herre", 1799),
              ("Recoverysko", 799)],
    "LOP02": [("Løpetights dame", 699), ("Løpetights herre", 699), ("Løpejakke vindtett", 1299), ("Løpeshorts dame", 449),
              ("Løpeshorts herre", 449), ("Løpetrøye ull", 799), ("Løpetrøye kortarm", 399), ("Løpelue", 249),
              ("Løpevotter", 299), ("Kompresjonsstrømper", 349), ("Løpevest refleks", 399), ("Sports-BH", 549)],
    "LOP03": [("Pulsklokke GPS", 3499), ("Pulsbelte", 699), ("Løpesekk 12 l", 1199), ("Løpebelte", 299),
              ("Drikkeflaske myk 500 ml", 199), ("Hodelykt 400 lm", 699), ("Refleksbånd 2-pk", 79),
              ("Brodder løp", 499), ("Sportsgel 6-pk", 149), ("Skolisser elastiske", 99), ("Massasjerulle", 349),
              ("Løpebrille", 899)],
    "FRI01": [("Telt 2 personer lett", 4999), ("Telt 3 personer", 5999), ("Lavvo 6 personer", 7999),
              ("Sovepose dun -10", 4499), ("Sovepose syntet 0", 1999), ("Liggeunderlag selvoppblåsende", 999),
              ("Liggeunderlag skum", 299), ("Hengekøye", 799), ("Tarp 3x3 m", 1199), ("Sovepose barn", 899),
              ("Teltunderlag", 499), ("Pute oppblåsbar", 249), ("Bivuakksekk", 1899)],
    "FRI02": [("Fjellstav karbon 120 cm", 1299), ("Fjellstav karbon 130 cm", 1349), ("Fjellstav aluminium 120 cm", 699),
              ("Fjellstav aluminium 135 cm", 749), ("Turstav sammenleggbar", 999), ("Stavtrinse vinter 2-pk", 149),
              ("Stavspiss hardmetall 2-pk", 129), ("Stavtrinse sommer 2-pk", 99), ("Langrennsstav karbon 150 cm", 1799),
              ("Langrennsstav aluminium 140 cm", 599), ("Stavhåndtak kork", 299), ("Juniorstav 110 cm", 349)],
    "FRI03": [("Dagstursekk 25 l", 1299), ("Dagstursekk 35 l", 1599), ("Fjellsekk 50 l", 2499), ("Fjellsekk 65 l", 2999),
              ("Toppturssekk 30 l", 1999), ("Bæremeis barn", 2799), ("Regntrekk sekk", 249), ("Pakkpose 10 l", 149),
              ("Skulderveske", 499), ("Hoftebelte tur", 399), ("Barnesekk 12 l", 499), ("Drybag 20 l", 349)],
    "SYK01": [("Terrengsykkel hardtail", 12999), ("Terrengsykkel fulldemper", 24999), ("Landeveissykkel aluminium", 14999),
              ("Grusracer", 17999), ("Bysykkel 7 gir", 6999), ("Barnesykkel 20 tommer", 3499), ("Barnesykkel 24 tommer", 3999),
              ("Elsykkel by", 29999), ("Elsykkel terreng", 39999), ("Hybridsykkel", 8999), ("Balansesykkel", 1499),
              ("Juniorsykkel terreng", 5999), ("Tandemsykkel", 18999)],
    "SYK02": [("Sykkelbukse med pute", 899), ("Sykkeltrøye kortarm", 699), ("Sykkeljakke vind", 1199),
              ("Sykkelhansker", 349), ("Vintersykkelhansker", 549), ("Sykkelsko terreng", 1499), ("Sykkelsko landevei", 1999),
              ("Skotrekk neopren", 399), ("Sykkelvest refleks", 449), ("Sykkelsokker 2-pk", 199), ("Sykkelbuff", 179),
              ("Regnbukse sykkel", 799)],
    "SYK03": [("Sykkelhjelm voksen", 999), ("Sykkelhjelm barn", 599), ("Sykkellås kraftig", 699), ("Sykkellykt basic", 199),
              ("Sykkellykt sett LED", 499), ("Sykkelpumpe gulv", 449), ("Slange 29 tommer", 99), ("Dekk terreng 29 tommer", 549),
              ("Sykkelcomputer GPS", 2999), ("Flaskeholder", 129), ("Sykkelveske bagasjebrett", 699), ("Kjedeolje", 119),
              ("Lappesett", 69)],
}
VARE_4711 = "Fjellstav karbon 120 cm"
VARE_H4 = ("Løpesekk 12 l", "LOP03", "FRI03")  # H4: bytter varegruppe i uttrekket 1. september
VARE_H6 = "Sykkellykt basic"  # H6: STATUS = U fra uttrekket 1. oktober (selges ikke fra 1. oktober)
VARE_H17 = "Terrengløpesko dame"  # H17: går tom i butikk 102 i uke 40
H17_BUTIKK = 102
H17_TOM = date(2026, 9, 29)       # en idrettslagsbestilling kjøper resten av beholdningen
H17_LEVERT = date(2026, 10, 5)    # ny leveranse mandag i uke 41
H17_BESTILT = 12
UTEN_MERKE = {"Skistropper 2-pk", "Refleksbånd 2-pk", "Lappesett"}  # MERKE tom i varesystemet
H3_NY_PRIS = Decimal("1399.00")
H3_FRA = VARE_UTTREKK[2]
H4_FRA = VARE_UTTREKK[1]
H6_FRA = VARE_UTTREKK[2]


def lag_varer():
    t = Trekk("varer")
    navn_liste = [(g, n, p) for g, _, _, _ in VAREGRUPPER for n, p in VARER_PER_GRUPPE[g]]
    assert len(navn_liste) == 150, len(navn_liste)
    brukt = {4711, 9999}
    nummer = []
    # to varer med tresifret nummer, resten firesifret; 4711 er fast (design.md), 9999 er ukjent (H8)
    while len(nummer) < 2:
        n = t.heltall(100, 999)
        if n not in brukt:
            brukt.add(n)
            nummer.append(n)
    while len(nummer) < 149:
        n = t.heltall(1000, 9899)
        if n not in brukt:
            brukt.add(n)
            nummer.append(n)
    nummer = t.stokk(nummer)
    varer = []
    i = 0
    for g, navn, pris in navn_liste:
        if navn == VARE_4711:
            nr, lev = 4711, 502
        else:
            nr = nummer[i]
            i += 1
            lev = t.velg([x for x in dict((k, l) for k, _, _, l in VAREGRUPPER)[g]])
        varer.append({
            "nr": nr, "tekst": navn, "gruppe": g, "lev": lev, "merke": "" if navn in UTEN_MERKE else MERKE[lev],
            "pris": Decimal(pris).quantize(KRONE), "status": "A",
            "vekt": (1000 / pris) ** 0.6 * (0.5 + t.tall()),
        })
    varer.sort(key=lambda v: v["nr"])
    return varer


def vare_paa(v: dict, tidspunkt: datetime) -> dict:
    """Varens rene verdier slik varesystemet har dem på et tidspunkt (H3, H4, H6)."""
    r = {"nr": v["nr"], "tekst": v["tekst"], "gruppe": v["gruppe"], "lev": v["lev"], "merke": v["merke"],
         "pris": v["pris"], "status": v["status"]}
    if v["nr"] == 4711 and tidspunkt >= H3_FRA:
        r["pris"] = H3_NY_PRIS
    if v["tekst"] == VARE_H4[0]:
        r["gruppe"] = VARE_H4[2] if tidspunkt >= H4_FRA else VARE_H4[1]
    if v["tekst"] == VARE_H6 and tidspunkt >= H6_FRA:
        r["status"] = "U"
    return r


def vare_dag(v: dict, d: date) -> dict:
    """Varens verdier som gjelder på salgsdatoen d (uttrekket kl. 05 den 1. gjelder fra den dagen)."""
    return vare_paa(v, datetime.combine(d, time(12, 0)))


# ---------------------------------------------------------------------------
# SANNHETEN: kundeklubben
# ---------------------------------------------------------------------------
FORNAVN = ["Ingrid", "Ola", "Kari", "Lars", "Anne", "Per", "Marte", "Jonas", "Sofie", "Henrik", "Nora", "Emil", "Ida",
           "Magnus", "Thea", "Sindre", "Live", "Eirik", "Hanne", "Kristian", "Maja", "Tobias", "Silje", "Håkon",
           "Astrid", "Mathias", "Vilde", "Øystein", "Ragnhild", "Andreas", "Tuva", "Sander", "Eva", "Bjørn", "Linn",
           "Fredrik", "Marit", "Even", "Synnøve", "Trond"]
ETTERNAVN = ["Haugen", "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen", "Kristiansen",
             "Jensen", "Karlsen", "Berg", "Dahl", "Lie", "Bakken", "Moen", "Strand", "Solberg", "Eide", "Lund",
             "Aas", "Hagen", "Brekke", "Sæther", "Rønning", "Fjeld", "Holm", "Nygård", "Vik", "Myhre"]
POSTNR = {  # butikk -> postnumre i nærheten
    101: ["0367", "0350", "0355", "0368", "0370", "0451", "0473", "0182", "0565", "0661"],
    102: ["5003", "5006", "5009", "5015", "5052", "5068", "5089", "5141", "5221", "5258"],
    103: ["7010", "7014", "7030", "7041", "7042", "7050", "7067", "7089", "7020", "7046"],
    104: ["4005", "4006", "4009", "4012", "4014", "4016", "4021", "4307", "4315", "4041"],
    105: ["9008", "9009", "9010", "9011", "9012", "9013", "9014", "9015", "9016", "9024"],
    106: ["2609", "2611", "2614", "2615", "2618", "2619", "2624", "2625", "2630", "2636"],
}
NIVA_RABATT = {"BRONZE": Decimal("0.05"), "SILVER": Decimal("0.10"), "GOLD": Decimal("0.15")}
FORSTE_MEDLEM = 300001
ANTALL_MEDLEMMER = 780
NYE_MEDLEMMER = 26
M42 = 300042
H14_GULL = date(2026, 9, 20)
H14_FLYTTER = date(2026, 10, 10)
H14_NYTT_POSTNR = "7014"
H15_DAG = date(2026, 10, 3)
H15_MEDLEM = 300999  # finnes ikke i kundeklubben
M42_KJOP_KASSE = [date(2026, 8, 15), date(2026, 9, 10), date(2026, 9, 26), date(2026, 10, 17)]
M42_KJOP_NETT = [date(2026, 8, 23), date(2026, 9, 6), date(2026, 10, 4), date(2026, 10, 24)]


def lag_medlemmer():
    t = Trekk("medlemmer")
    medlemmer = []
    for i in range(ANTALL_MEDLEMMER + NYE_MEDLEMMER):
        nr = FORSTE_MEDLEM + i
        hjem = t.vektet(FYSISKE[:5], [BUTIKKVEKT[b] for b in FYSISKE[:5]])
        if i < ANTALL_MEDLEMMER:
            innmeldt = date(2016, 1, 1) + timedelta(days=t.heltall(0, (date(2026, 7, 30) - date(2016, 1, 1)).days))
            niva = t.vektet(["BRONZE", "SILVER", "GOLD"], [0.6, 0.28, 0.12])
        else:
            innmeldt = date(2026, 8, 1) + timedelta(days=t.heltall(0, (date(2026, 10, 27) - date(2026, 8, 1)).days))
            niva = "BRONZE"
            if t.tall() < 0.3:
                hjem = LILLEHAMMER
                innmeldt = max(innmeldt, LILLEHAMMER_APNER)
        m = {"nr": nr, "fornavn": t.velg(FORNAVN), "etternavn": t.velg(ETTERNAVN), "postnr": t.velg(POSTNR[hjem]),
             "niva": niva, "innmeldt": innmeldt, "hjem": hjem,
             "aktivitet": {"BRONZE": 1.0, "SILVER": 2.0, "GOLD": 3.2}[niva] * (0.3 + t.tall())}
        if nr == M42:
            m.update(fornavn="Ingrid", etternavn="Haugen", postnr="0367", niva="SILVER", innmeldt=date(2024, 3, 15), hjem=101)
        medlemmer.append(m)
    return medlemmer


def i_uttrekk_fra(m: dict) -> date:
    """Første dag medlemmet står i uttrekket kl. 04 (dagen etter innmelding; de eldste fra første uttrekk)."""
    return max(FRA, m["innmeldt"] + timedelta(days=1))


def kan_handle_fra(m: dict) -> date:
    """Nye medlemmer handler tidligst dagen etter at de første gang står i uttrekket."""
    return FRA if m["innmeldt"] < FRA else i_uttrekk_fra(m) + timedelta(days=1)


def medlem_paa(m: dict, d: date) -> dict:
    """Medlemmets rene verdier i uttrekket dag d kl. 04 (H14)."""
    r = {"nr": m["nr"], "fornavn": m["fornavn"], "etternavn": m["etternavn"], "postnr": m["postnr"],
         "niva": m["niva"], "innmeldt": m["innmeldt"]}
    if m["nr"] == M42:
        if d >= H14_GULL:
            r["niva"] = "GOLD"
        if d >= H14_FLYTTER:
            r["postnr"] = H14_NYTT_POSTNR
    return r


# ---------------------------------------------------------------------------
# Kalender (helligdager i Norge 2026-2027)
# ---------------------------------------------------------------------------
def paaskedag(aar: int) -> date:
    a, b, c = aar % 19, aar // 100, aar % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    mnd = (h + l_ - 7 * m + 114) // 31
    dag = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(aar, mnd, dag)


def helligdager(aar: int) -> set:
    p = paaskedag(aar)
    return {date(aar, 1, 1), p - timedelta(days=3), p - timedelta(days=2), p, p + timedelta(days=1), date(aar, 5, 1),
            date(aar, 5, 17), p + timedelta(days=39), p + timedelta(days=49), p + timedelta(days=50),
            date(aar, 12, 25), date(aar, 12, 26)}


def lag_kalender():
    hellig = helligdager(2026) | helligdager(2027)
    rader = []
    d = date(2026, 1, 1)
    while d <= date(2027, 12, 31):
        rader.append({"DATO": d.isoformat(), "UKEDAG": UKEDAGER[d.weekday()], "UKE": str(d.isocalendar()[1]),
                      "MND": str(d.month), "KVARTAL": str((d.month - 1) // 3 + 1), "AAR": str(d.year),
                      "HELLIGDAG": "J" if d in hellig else "N"})
        d += timedelta(days=1)
    return rader


# ---------------------------------------------------------------------------
# Simulering: salg i butikk, nettsalg og lager, dag for dag
# ---------------------------------------------------------------------------
KVITTERINGER_PER_DAG = 250
UKEDAGSFAKTOR = [0.9, 0.9, 0.95, 1.05, 1.1, 1.1, 0.0]  # søndag stengt
APNINGSTID = {0: (10, 20), 1: (10, 20), 2: (10, 20), 3: (10, 20), 4: (10, 20), 5: (10, 18)}
# H13: kjøp rett etter midnatt norsk tid, da UTC-tidspunktet er dagen før. (dato, butikk, antall kvitteringer)
MIDNATTSAPNING = [
    (date(2026, 8, 29), 101, 12),   # midnattssalg på Majorstuen
    (date(2026, 9, 5), 106, 24),    # Lillehammer åpner ved midnatt (H5 + H13: første soldAt er 4. september UTC)
    (date(2026, 10, 31), 104, 8),   # etter overgangen til vintertid (UTC+1)
]
H8_DAG = date(2026, 8, 14)
H8_LINJER = 6
H8_PRIS = Decimal("349.00")
H11_DAG = date(2026, 8, 21)
KAMPANJE = ("HOST26", date(2026, 10, 1), date(2026, 10, 18), {"FRI01", "FRI03"}, Decimal("0.20"))
RETUR_ANDEL = 0.0205
MEDLEM_ANDEL_KASSE = 0.60
NETTORDRER_PER_DAG = 40
NETT_TIMEVEKT = [2, 1, 0.5, 0.3, 0.3, 0.5, 1, 2, 3, 3, 3, 3, 4, 3, 3, 3, 3, 3, 4, 5, 6, 6, 5, 3]
FORSTE_ORDRE = 5201
LEVERINGSDAGER = 3


def sesongvekt(v: dict, d: date) -> float:
    aug, okt = SESONG[HOVEDGRUPPE[v["gruppe"]]]
    x = (d - FRA).days / (TIL - FRA).days
    return v["vekt"] * (aug + (okt - aug) * x)


def utc_fra_lokal(d: date, sekunder: int) -> datetime:
    lokal = datetime.combine(d, time(0, 0), tzinfo=OSLO) + timedelta(seconds=sekunder)
    # kombiner på nytt for riktig UTC-forskyvning (sommer- og vintertid)
    lokal = datetime(lokal.year, lokal.month, lokal.day, lokal.hour, lokal.minute, lokal.second, tzinfo=OSLO)
    return lokal.astimezone(UTC).replace(tzinfo=None)


def norsk_dato(utc: datetime) -> date:
    return utc.replace(tzinfo=UTC).astimezone(OSLO).date()


def simuler(varer, medlemmer):
    t = Trekk("salg")
    tn = Trekk("nett")
    tl = Trekk("lager")
    vare_paa_nr = {v["nr"]: v for v in varer}
    medlem_nr = {m["nr"]: m for m in medlemmer}
    h17 = next(v["nr"] for v in varer if v["tekst"] == VARE_H17)
    h6 = next(v["nr"] for v in varer if v["tekst"] == VARE_H6)

    # lagerstatus: (butikk, vare) -> dict
    lager = {}

    def start_lager(b):
        for v in varer:
            if (b, v["nr"]) == (H17_BUTIKK, h17):
                beh = 9
            elif v["pris"] >= 1500:
                beh = tl.heltall(3, 8)
            else:
                beh = tl.heltall(5, 16)
            lager[(b, v["nr"])] = {"on_hand": beh, "on_order": 0, "kommer": None}

    kvitteringer = []   # rene kvitteringshoder
    kasselinjer = []    # rene kvitteringslinjer
    nettlinjer = []     # rene ordrelinjer
    lager_dag = {}      # (dato, butikk, vare) -> (on_hand, on_order) ved dagens slutt, alle dager
    ordre_seq = FORSTE_ORDRE
    vare_ids = [v["nr"] for v in varer]

    for d in DAGER:
        apne = [b for b in FYSISKE if d.weekday() != 6 and (b != LILLEHAMMER or d >= LILLEHAMMER_APNER)]
        if d == LILLEHAMMER_APNER:
            start_lager(LILLEHAMMER)
        if d == FRA:
            for b in FYSISKE[:5]:
                start_lager(b)
        # leveranser kommer om morgenen
        for (b, nr), s in lager.items():
            if s["kommer"] is not None and s["kommer"] <= d and d.weekday() != 6:
                s["on_hand"] += s["on_order"]
                s["on_order"] = 0
                s["kommer"] = None

        dagvarer = {nr: vare_dag(vare_paa_nr[nr], d) for nr in vare_ids}
        selgbare = [nr for nr in vare_ids if dagvarer[nr]["status"] == "A" and not (nr == h6 and d >= H6_FRA.date())]
        vekter = [sesongvekt(vare_paa_nr[nr], d) for nr in selgbare]
        mulige = [m for m in medlemmer if kan_handle_fra(m) <= d and m["nr"] != M42]
        mvekt = [m["aktivitet"] * (1.6 if m["hjem"] == LILLEHAMMER else 1.0) for m in mulige]

        def niva(nr):
            return medlem_paa(medlem_nr[nr], d)["niva"]

        # ---- kasse ----
        total = KVITTERINGER_PER_DAG * UKEDAGSFAKTOR[d.weekday()]
        sumvekt = sum(BUTIKKVEKT[b] for b in apne) or 1
        dagens_kv = []
        for b in apne:
            n = total * BUTIKKVEKT[b] / sumvekt
            if b == LILLEHAMMER and d == LILLEHAMMER_APNER:
                n *= 1.6
            n = int(round(n * (0.88 + 0.24 * t.tall())))
            fra_t, til_t = APNINGSTID[d.weekday()]
            spesifikasjoner = [{"sek": t.heltall(fra_t * 3600, til_t * 3600 - 1)} for _ in range(n)]
            for md, mb, antall in MIDNATTSAPNING:
                if md == d and mb == b:
                    spesifikasjoner += [{"sek": t.heltall(5 * 60, 59 * 60)} for _ in range(antall)]
            if b == 101 and d in M42_KJOP_KASSE:
                spesifikasjoner.append({"sek": 12 * 3600 + 30 * 60 + t.heltall(0, 900), "medlem": M42})
            if b == H17_BUTIKK and d == H17_TOM:
                spesifikasjoner.append({"sek": 14 * 3600 + 12 * 60 + 41, "h17": True})
            spesifikasjoner.sort(key=lambda s: s["sek"])
            for seq, sp in enumerate(spesifikasjoner, start=1):
                kv = {"butikk": b, "nr": f"{d.strftime('%Y%m%d')}-{b}-{seq:04d}", "dato": d,
                      "solgt": utc_fra_lokal(d, sp["sek"]), "medlem": None, "betaling": None, "linjer": []}
                if "medlem" in sp:
                    kv["medlem"] = sp["medlem"]
                elif not sp.get("h17") and t.tall() < MEDLEM_ANDEL_KASSE:
                    kv["medlem"] = t.vektet(mulige, mvekt)["nr"]
                kv["betaling"] = t.vektet(["CARD", "VIPPS", "CASH"], [0.7, 0.2, 0.1])
                m_niva = niva(kv["medlem"]) if kv["medlem"] is not None else None
                if sp.get("h17"):
                    s = lager[(b, h17)]
                    linjer = [(h17, s["on_hand"])]
                else:
                    antall_linjer = t.vektet([1, 2, 3, 4], [0.42, 0.31, 0.17, 0.10])
                    linjer = []
                    brukt = set()
                    for _ in range(antall_linjer):
                        retur = t.tall() < RETUR_ANDEL
                        for _forsok in range(30):
                            nr = t.vektet(selgbare, vekter)
                            if nr in brukt:
                                continue
                            pris = dagvarer[nr]["pris"]
                            if retur:
                                q = -2 if t.tall() < 0.1 and pris < 1000 else -1
                            else:
                                x = t.tall()
                                q = 1 if pris >= 1500 or x < 0.85 else (2 if x < 0.97 else 3)
                            s = lager[(b, nr)]
                            minst = 2 if (b, nr) == (H17_BUTIKK, h17) else 1
                            if (b, nr) == (H17_BUTIKK, h17) and H17_TOM <= d < H17_LEVERT:
                                continue
                            if q > 0 and s["on_hand"] - q < minst:
                                continue
                            brukt.add(nr)
                            linjer.append((nr, q))
                            break
                for nr, q in linjer:
                    pris = dagvarer[nr]["pris"]
                    kode = ""
                    sats = Decimal(0)
                    k_kode, k_fra, k_til, k_grupper, k_sats = KAMPANJE
                    if k_fra <= d <= k_til and dagvarer[nr]["gruppe"] in k_grupper:
                        kode, sats = k_kode, k_sats
                    elif m_niva is not None:
                        sats = NIVA_RABATT[m_niva]
                    rabatt = kr(abs(q) * pris * sats) * (1 if q > 0 else -1) if sats else Decimal("0.00")
                    lager[(b, nr)]["on_hand"] -= q
                    kv["linjer"].append({"sku": nr, "antall": q, "pris": pris, "rabatt": rabatt, "kampanje": kode})
                dagens_kv.append(kv)
        # H8: ukjent varenummer 9999 på noen linjer 14. august (ikke i varesystemet, ikke i lageret)
        if d == H8_DAG:
            kandidater = [kv for kv in dagens_kv if len(kv["linjer"]) < 4]  # en kvittering har høyst fire linjer
            valgt = [kandidater[int(len(kandidater) * (i + 0.5) / H8_LINJER)] for i in range(H8_LINJER)]
            for kv in valgt:
                kv["linjer"].append({"sku": 9999, "antall": 1, "pris": H8_PRIS, "rabatt": Decimal("0.00"), "kampanje": ""})
        for kv in dagens_kv:
            kvitteringer.append(kv)
            for i, ln in enumerate(kv["linjer"], start=1):
                kasselinjer.append({"kanal": "Butikk", "butikk": kv["butikk"], "salgsnummer": kv["nr"], "linje": i,
                                    "solgt": kv["solgt"], "dato": kv["dato"], "vare": ln["sku"], "medlem": kv["medlem"],
                                    "antall": ln["antall"], "pris": ln["pris"], "rabatt": ln["rabatt"],
                                    "kampanje": ln["kampanje"], "belop": ln["antall"] * ln["pris"] - ln["rabatt"]})

        # ---- nettora (hver dag, også søndag) ----
        n = int(round(NETTORDRER_PER_DAG * (1.15 if d.weekday() == 6 else 1.0) * (0.85 + 0.3 * tn.tall())))
        ordrer = [{"sek": tn.vektet(list(range(24)), NETT_TIMEVEKT) * 3600 + tn.heltall(0, 3599)} for _ in range(n)]
        if d in M42_KJOP_NETT:
            ordrer.append({"sek": 20 * 3600 + 15 * 60 + tn.heltall(0, 600), "medlem": M42})
        if d == H15_DAG:
            ordrer.append({"sek": 19 * 3600 + 42 * 60 + 7, "medlem": H15_MEDLEM})
        ordrer.sort(key=lambda o: o["sek"])
        nett_selgbare = selgbare
        for o in ordrer:
            medlem = o.get("medlem") or tn.vektet(mulige, mvekt)["nr"]
            if medlem == H15_MEDLEM:
                sats = Decimal(0)
            else:
                sats = NIVA_RABATT[niva(medlem)]
            ordrenr = f"N-2026-{ordre_seq:06d}"
            ordre_seq += 1
            solgt = utc_fra_lokal(d, o["sek"])
            antall_linjer = 2 if medlem == H15_MEDLEM else tn.vektet([1, 2, 3], [0.6, 0.3, 0.1])
            brukt = set()
            linje = 0
            while linje < antall_linjer:
                nr = tn.vektet(nett_selgbare, vekter)
                if nr in brukt:
                    continue
                brukt.add(nr)
                linje += 1
                pris = kr(dagvarer[nr]["pris"] * (1 - sats))
                q = 2 if tn.tall() < 0.1 and pris < 1000 else 1
                nettlinjer.append({"kanal": "Nett", "butikk": NETTBUTIKK, "salgsnummer": ordrenr, "linje": linje,
                                   "solgt": solgt, "dato": d, "vare": nr, "medlem": medlem, "antall": q,
                                   "pris": pris, "rabatt": Decimal("0.00"), "kampanje": "", "belop": q * pris})

        # ---- lager: bestilling ved dagens slutt (tellingsdager), så øyeblikksbilde ----
        if er_tellingsdag(d):
            for (b, nr), s in lager.items():
                if (b, nr) == (H17_BUTIKK, h17):
                    if d == H17_TOM:
                        assert s["on_hand"] == 0
                        s["on_order"], s["kommer"] = H17_BESTILT, H17_LEVERT
                    continue
                if s["on_hand"] <= 2 and s["on_order"] == 0 and nr != h6:
                    s["on_order"] = tl.heltall(8, 15)
                    kommer = d + timedelta(days=LEVERINGSDAGER)
                    if kommer.weekday() == 6:
                        kommer += timedelta(days=1)
                    s["kommer"] = kommer
        for (b, nr), s in lager.items():
            assert s["on_hand"] >= 0
            lager_dag[(d, b, nr)] = (s["on_hand"], s["on_order"])
    return kvitteringer, kasselinjer, nettlinjer, lager_dag, h17, h6


# ---------------------------------------------------------------------------
# Landingsfilene (skrivemåtene til hver kilde)
# ---------------------------------------------------------------------------
def kr_komma(x: Decimal) -> str:
    return f"{x:.2f}".replace(".", ",")


def ddmmyyyy(d: date | None) -> str:
    return "" if d is None else d.strftime("%d.%m.%Y")


def iso_utc(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


class Tall:
    """Desimaltall som skrives med nøyaktig to desimaler i JSON (1169.10, ikke 1169.1)."""
    def __init__(self, d: Decimal):
        self.s = f"{d:.2f}"


def json_linje(post: dict) -> str:
    deler = []
    for k, v in post.items():
        verdi = v.s if isinstance(v, Tall) else json.dumps(v, ensure_ascii=False)
        deler.append(f"{json.dumps(k)}: {verdi}")
    return "{" + ", ".join(deler) + "}"


def skriv_csv(sti, kolonner, rader, sep):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=sep, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(kolonner)
    for r in rader:
        w.writerow([r[k] for k in kolonner])
    with open(sti, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())


def skriv_json(sti, rader):
    with open(sti, "w", encoding="utf-8", newline="") as f:
        for r in rader:
            f.write(json_linje(r) + "\n")


def skriv_parquet(sti, rader):
    import pyarrow as pa
    import pyarrow.parquet as pq
    skjema = pa.schema([("whs_store", pa.int32()), ("item_no", pa.int32()), ("count_date", pa.date32()),
                        ("on_hand", pa.int32()), ("on_order", pa.int32())])
    pq.write_table(pa.Table.from_pylist(rader, schema=skjema), sti, compression="snappy")


def lag_filer(varer, medlemmer, kvitteringer, kasselinjer, nettlinjer, lager_dag, kalender):
    """-> {relativ sti: (nøkkel, kolonner, rader)} med rader slik de står i filen."""
    filer = {}

    def legg(nokkel, ankomst, kolonner, rader):
        sti = filsti(nokkel, ankomst)
        assert sti not in filer, sti
        filer[sti] = (nokkel, kolonner, rader)

    # varius: fulle uttrekk den 1. hver måned kl. 05 (H1, H2, H3, H4, H5, H6)
    for u in VARE_UTTREKK:
        legg("varius__vare", u, KOLONNER["varius__vare"], [
            {"VARENR": f"{r['nr']:06d}", "VARETEKST": r["tekst"], "VGRP": r["gruppe"], "LEVNR": str(r["lev"]),
             "MERKE": r["merke"], "UTPRIS": kr_komma(r["pris"]), "STATUS": r["status"]}
            for r in (vare_paa(v, u) for v in varer)])
        legg("varius__varegruppe", u, KOLONNER["varius__varegruppe"], [
            {"VGRP": k, "VGRP_TEKST": tekst, "HOVEDGRP": h} for k, tekst, h, _ in VAREGRUPPER])
        aktorer = []
        for nr, navn, kommune, apnet in BUTIKKER:
            if nr == LILLEHAMMER and u < LILLEHAMMER_I_VARESYSTEM:
                continue
            aktorer.append({"AKTNR": str(nr), "AKTTYPE": "B", "NAVN": navn, "KOMMUNE": kommune,
                            "AAPNET_DT": ddmmyyyy(apnet), "ORGNR": ""})
        for nr, navn, kommune, orgnr, _ in LEVERANDORER:
            aktorer.append({"AKTNR": str(nr), "AKTTYPE": "L", "NAVN": navn, "KOMMUNE": kommune, "AAPNET_DT": "",
                            "ORGNR": orgnr})
        legg("varius__aktor", u, KOLONNER["varius__aktor"], aktorer)

    # kasse: daglig fil kl. 06 for gårsdagen (H7-H13); søndager er butikkene stengt (filen har bare overskrift)
    kv_per_dag = defaultdict(list)
    for kv in kvitteringer:
        kv_per_dag[kv["dato"]].append(kv)
    for d in DAGER:
        ankomst = kasse_ankomst(d)
        dagens = sorted(kv_per_dag[d], key=lambda k: (k["butikk"], k["nr"]))
        legg("kassio__kvittering", ankomst, KOLONNER["kassio__kvittering"], [
            {"storeId": str(k["butikk"]), "receiptNo": k["nr"], "soldAt": iso_utc(k["solgt"]),
             "memberNo": "" if k["medlem"] is None else str(k["medlem"]), "paymentType": k["betaling"]} for k in dagens])
        kol = KOLONNER["kassio__kvitteringslinje"] + (["campaignCode"] if d >= H10_FRA else [])
        linjer = []
        for k in dagens:
            for i, ln in enumerate(k["linjer"], start=1):
                r = {"storeId": str(k["butikk"]), "receiptNo": k["nr"], "lineNo": str(i), "sku": str(ln["sku"]),
                     "qty": str(ln["antall"]), "unitPrice": f"{ln['pris']:.2f}", "discount": f"{ln['rabatt']:.2f}"}
                if d >= H10_FRA:
                    r["campaignCode"] = ln["kampanje"]
                linjer.append(r)
        if d == H11_DAG:  # H11: den samme linjen to ganger i filen
            idx = len(linjer) // 3
            linjer.insert(idx + 1, dict(linjer[idx]))
        legg("kassio__kvitteringslinje", ankomst, kol, linjer)

    # nettora: daglig fil kl. 06 for gårsdagen (H13, H15)
    nett_per_dag = defaultdict(list)
    for ln in nettlinjer:
        nett_per_dag[ln["dato"]].append(ln)
    for d in DAGER:
        legg("nettora__ordrelinje", nett_ankomst(d), KOLONNER["nettora__ordrelinje"], [
            {"order_id": ln["salgsnummer"], "line_no": ln["linje"], "customer_id": ln["medlem"],
             "ordered_at": iso_utc(ln["solgt"]), "product_code": f"{ln['vare']:06d}", "quantity": ln["antall"],
             "price": Tall(ln["pris"])} for ln in nett_per_dag[d]])

    # lojal: fullt uttrekk hver dag kl. 04 (H14)
    for d in DAGER:
        rader = []
        for m in medlemmer:
            if i_uttrekk_fra(m) > d:
                continue
            r = medlem_paa(m, d)
            rader.append({"memberId": r["nr"], "firstName": r["fornavn"], "lastName": r["etternavn"],
                          "postalCode": r["postnr"], "tier": r["niva"], "joinedDate": r["innmeldt"].isoformat()})
        legg("lojal__medlem", klubb_uttrekk(d), KOLONNER["lojal__medlem"], rader)

    # lagra: telling mandag til lørdag kl. 23 (H16, H17)
    for d in DAGER:
        if not er_tellingsdag(d):
            continue
        rader = []
        for b in FYSISKE:
            if b == LILLEHAMMER and d < LILLEHAMMER_APNER:
                continue
            for v in varer:
                on_hand, on_order = lager_dag[(d, b, v["nr"])]
                rader.append({"whs_store": b, "item_no": v["nr"], "count_date": d, "on_hand": on_hand, "on_order": on_order})
        legg("lagra__beholdning", lager_telling(d), KOLONNER["lagra__beholdning"], rader)

    legg("kalender__dag", KALENDER_FIL, KOLONNER["kalender__dag"], kalender)
    return filer


def skriv_landing(rot, filer):
    for sti, (nokkel, kolonner, rader) in sorted(filer.items()):
        full = os.path.join(rot, sti)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        ext = TABELLER[nokkel][2]
        if ext == "csv":
            skriv_csv(full, kolonner, rader, SKILLETEGN[TABELLER[nokkel][0]])
        elif ext == "json":
            skriv_json(full, rader)
        else:
            skriv_parquet(full, rader)


# ---------------------------------------------------------------------------
# FASIT: regnet fra sannheten
# ---------------------------------------------------------------------------
def tall(x: Decimal) -> float:
    return float(kr(x))


def uke(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def scd2_antall(snapshots):
    """snapshots: [(tidspunkt, {bk: verdier})] i rekkefølge (fulle uttrekk). -> {bk: [versjoner]}"""
    apne, alle = {}, defaultdict(list)
    for tidspunkt, rader in snapshots:
        for k in list(apne):
            if k not in rader:
                apne.pop(k)["til"] = tidspunkt
        for k, verdier in rader.items():
            if k in apne and apne[k]["verdier"] == verdier:
                continue
            if k in apne:
                apne[k]["til"] = tidspunkt
            v = {"verdier": verdier, "fra": tidspunkt, "til": None}
            apne[k] = v
            alle[k].append(v)
    return alle


def lag_fasit(varer, medlemmer, kvitteringer, kasselinjer, nettlinjer, lager_dag, kalender, filer, h17, h6):
    f = {"om": {
        "generator": "tools/lag_data.py", "seed": SEED, "periode": [FRA.isoformat(), TIL.isoformat()],
        "salgsdato": "norsk dato (Europe/Oslo) av soldAt/ordered_at, ikke filens dato",
        "belop": "antall * enhetspris - rabatt, kroner med mva; nettbutikkens pris er etter rabatt, rabatt 0",
        "regnet_fra": "generatorens sannhet, ikke filene og ikke pipelinen",
    }}
    alle_linjer = kasselinjer + nettlinjer
    vare_nr = {v["nr"]: v for v in varer}
    sist = VARE_UTTREKK[-1]
    gruppe_scd1 = {nr: vare_paa(v, sist)["gruppe"] for nr, v in vare_nr.items()}
    gruppenavn = {k: n for k, n, _, _ in VAREGRUPPER}
    medlem_nr = {m["nr"]: m for m in medlemmer}

    # ---- filer og raw (modul 2) ----
    per_tabell = defaultdict(lambda: {"filer": 0, "rader": 0})
    for sti, (nokkel, _, rader) in filer.items():
        per_tabell[f"raw__{nokkel}"]["filer"] += 1
        per_tabell[f"raw__{nokkel}"]["rader"] += len(rader)
    f["filer"] = {"antall": len(filer), "per_fil": {sti: len(r) for sti, (_, _, r) in sorted(filer.items())}}
    f["modul2_raw"] = {"rader_per_tabell": dict(sorted(per_tabell.items()))}

    # ---- bronze (modul 3) ----
    # Fulle uttrekk: SCD2 over de rene verdiene (filradene er bare skrivemåten av dem; samme rekkefølge).
    vare_snap = [(u.isoformat(), {(v["nr"],): tuple(sorted(vare_paa(v, u).items())) for v in varer}) for u in VARE_UTTREKK]
    vare_v = scd2_antall(vare_snap)
    gruppe_v = scd2_antall([(u.isoformat(), {(k,): (t_, h) for k, t_, h, _ in VAREGRUPPER}) for u in VARE_UTTREKK])
    aktor_v = scd2_antall([(u.isoformat(), {(nr,): (navn, kommune, apnet) for nr, navn, kommune, apnet in BUTIKKER
                                            if not (nr == LILLEHAMMER and u < LILLEHAMMER_I_VARESYSTEM)}
                            | {(nr,): (navn, kommune, orgnr) for nr, navn, kommune, orgnr, _ in LEVERANDORER})
                           for u in VARE_UTTREKK])
    medlem_v = scd2_antall([(klubb_uttrekk(d).isoformat(), {(m["nr"],): tuple(sorted(medlem_paa(m, d).items(), key=str))
                                                             for m in medlemmer if i_uttrekk_fra(m) <= d}) for d in DAGER])
    lager_v = scd2_antall([(lager_telling(d).isoformat(), {(b, nr): (d,) + lager_dag[(d, b, nr)]
                                                           for b in FYSISKE for nr in vare_nr
                                                           if not (b == LILLEHAMMER and d < LILLEHAMMER_APNER)})
                           for d in DAGER if er_tellingsdag(d)])
    n_kasselinjer = len(kasselinjer)
    rader_bronze = {
        "brz__varius__vare": sum(len(v) for v in vare_v.values()),
        "brz__varius__varegruppe": sum(len(v) for v in gruppe_v.values()),
        "brz__varius__aktor": sum(len(v) for v in aktor_v.values()),
        "brz__kassio__kvittering": len(kvitteringer),
        "brz__kassio__kvitteringslinje": n_kasselinjer,
        "brz__nettora__ordrelinje": len(nettlinjer),
        "brz__lojal__medlem": sum(len(v) for v in medlem_v.values()),
        "brz__lagra__beholdning": sum(len(v) for v in lager_v.values()),
        "brz__kalender__dag": len(kalender),
    }
    v4711 = [{"UTPRIS": tall(dict(v["verdier"])["pris"]), "fra_uttrekk": v["fra"], "til_uttrekk": v["til"]}
             for v in vare_v[(4711,)]]
    endret = {f"{k[0]:06d}": len(v) for k, v in vare_v.items() if len(v) > 1}
    h11_fil = filsti("kassio__kvitteringslinje", kasse_ankomst(H11_DAG))
    f["modul3_bronze"] = {
        "rader_per_tabell": rader_bronze,
        "gjeldende_rader": {"brz__varius__vare": len(vare_v), "brz__varius__aktor": len(aktor_v),
                            "brz__lojal__medlem": len(medlem_v), "brz__lagra__beholdning": len(lager_v)},
        "vare_004711_versjoner": v4711,
        "varer_med_flere_versjoner": endret,
        "kvitteringslinje_raw_minus_bronze": per_tabell["raw__kassio__kvitteringslinje"]["rader"] - n_kasselinjer,
        "h11_fil": h11_fil,
    }

    # ---- sølv (modul 4) ----
    def per_butikk_dato(linjer):
        ut = defaultdict(lambda: defaultdict(lambda: [0, Decimal(0)]))
        for ln in linjer:
            x = ut[ln["dato"].isoformat()][str(ln["butikk"])]
            x[0] += 1
            x[1] += ln["belop"]
        return {d: {b: {"linjer": x[0], "belop": tall(x[1])} for b, x in sorted(bs.items())} for d, bs in sorted(ut.items())}

    utc_annen_dato = [ln for ln in kasselinjer if ln["solgt"].date() != ln["dato"]]
    utc_annen_dato_kv = sorted({(ln["butikk"], ln["salgsnummer"]) for ln in utc_annen_dato})
    lh = [ln for ln in kasselinjer if ln["butikk"] == LILLEHAMMER]
    valgte = ["2026-08-14", "2026-08-21", "2026-08-29", "2026-09-05", "2026-09-12", "2026-09-29", "2026-10-01", "2026-10-31"]
    kasse_pbd = per_butikk_dato(kasselinjer)
    f["modul4_solv"] = {
        "slv__salgslinje_rader_kasse": len(kasselinjer),
        "slv__butikk_rader": len(BUTIKKER), "slv__leverandor_rader": len(LEVERANDORER),
        "slv__produkt_rader": len(varer), "slv__produktgruppe_rader": len(VAREGRUPPER),
        "fb__slv__produkt_uten_treff": {"linjer": sum(1 for ln in kasselinjer if ln["vare"] not in vare_nr), "varenummer": "9999",
                                   "salgsdato": H8_DAG.isoformat()},
        "lillehammer": {"forste_salgsdato": min(ln["dato"] for ln in lh).isoformat(),
                        "forste_solgt_tidspunkt_utc": iso_utc(min(ln["solgt"] for ln in lh)),
                        "linjer": len(lh)},
        "h12_salgsdato_2026_09_12": {"fil": filsti("kassio__kvitteringslinje", SEN_ANKOMST),
                                     "linjer": sum(1 for ln in kasselinjer if ln["dato"] == SEN_DAG)},
        "h13_kasse": {"linjer_utc_dato_ulik_salgsdato": len(utc_annen_dato),
                      "kvitteringer": len(utc_annen_dato_kv)},
        "salgslinjer_per_butikk_valgte_datoer": {d: kasse_pbd.get(d, {}) for d in valgte},
        "salgslinjer_per_butikk_per_dato": kasse_pbd,
    }
    per_dato = defaultdict(int)
    for ln in utc_annen_dato:
        per_dato[ln["dato"].isoformat()] += 1
    f["modul4_solv"]["h13_kasse"]["per_salgsdato"] = dict(sorted(per_dato.items()))

    # ---- gull salg (modul 5) ----
    def omsetning(linjer):
        ut = defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal)))
        for ln in linjer:
            g = gruppe_scd1.get(ln["vare"], "-1")
            ut[uke(ln["dato"])][str(ln["butikk"])][g] += ln["belop"]
        return {u: {b: {g: tall(x) for g, x in sorted(gs.items())} for b, gs in sorted(bs.items())} for u, bs in sorted(ut.items())}

    retur = [ln for ln in kasselinjer if ln["antall"] < 0]
    h4_nr = next(v["nr"] for v in varer if v["tekst"] == VARE_H4[0])
    h4_foer = [ln for ln in kasselinjer + nettlinjer if ln["vare"] == h4_nr and ln["dato"] < H4_FRA.date()]
    sum_kasse = sum((ln["belop"] for ln in kasselinjer), Decimal(0))
    per_butikk = defaultdict(Decimal)
    for ln in kasselinjer:
        per_butikk[str(ln["butikk"])] += ln["belop"]
    per_gruppe = defaultdict(Decimal)
    for ln in kasselinjer:
        per_gruppe[gruppe_scd1.get(ln["vare"], "-1")] += ln["belop"]
    retur_butikk = defaultdict(lambda: [0, 0, Decimal(0)])
    for ln in retur:
        x = retur_butikk[str(ln["butikk"])]
        x[0] += 1
        x[1] += ln["antall"]
        x[2] += ln["belop"]
    h6_linjer = [ln for ln in alle_linjer if ln["vare"] == h6]
    f["modul5_gull_salg"] = {
        "gld__f__salg_rader_kasse": len(kasselinjer),
        "gld__d__produkt_rader_uten_minus": len(varer), "gld__d__butikk_rader_uten_minus": len(BUTIKKER),
        "fk__gld__d__produkt": {"-1": sum(1 for ln in kasselinjer if ln["vare"] not in vare_nr), "-2": 0},
        "belop_totalt_kasse": tall(sum_kasse),
        "belop_per_butikk_kasse": {b: tall(x) for b, x in sorted(per_butikk.items())},
        "belop_per_varegruppe_kasse_scd1": {g: tall(x) for g, x in sorted(per_gruppe.items())},
        "retur": {"linjer": len(retur), "andel_av_kasselinjer": round(len(retur) / len(kasselinjer), 4),
                  "antall_sum": sum(ln["antall"] for ln in retur),
                  "belop_sum": tall(sum((ln["belop"] for ln in retur), Decimal(0))),
                  "per_butikk": {b: {"linjer": x[0], "antall": x[1], "belop": tall(x[2])} for b, x in sorted(retur_butikk.items())}},
        "h3_004711": {"pris_til_og_med_2026_09_30": 1299.0, "pris_fra_2026_10_01": float(H3_NY_PRIS),
                      "gld__d__produkt_utpris_scd1": float(H3_NY_PRIS),
                      "salgslinjer_kasse_foer_okt": sum(1 for ln in kasselinjer if ln["vare"] == 4711 and ln["dato"] < H3_FRA.date()),
                      "salgslinjer_kasse_fra_okt": sum(1 for ln in kasselinjer if ln["vare"] == 4711 and ln["dato"] >= H3_FRA.date())},
        "h4_gruppebytte": {"varenummer": str(h4_nr), "fra": VARE_H4[1], "til": VARE_H4[2], "fra_uttrekk": H4_FRA.isoformat(),
                           "linjer_foer_bytte_alle_kanaler": len(h4_foer),
                           "belop_foer_bytte_alle_kanaler": tall(sum((ln["belop"] for ln in h4_foer), Decimal(0))),
                           "merknad": "SCD1: gammelt salg telles i den nye gruppen i omsetningen per varegruppe"},
        "h6_utgatt": {"varenummer": str(h6), "er_aktiv": False, "linjer_alle_kanaler": len(h6_linjer),
                      "siste_salgsdato": max(ln["dato"] for ln in h6_linjer).isoformat()},
        "omsetning_uke_butikk_varegruppe_kasse": omsetning(kasselinjer),
        "varegruppenavn": gruppenavn | {"-1": "Ukjent"},
    }

    # ---- nett (modul 6) ----
    sum_nett = sum((ln["belop"] for ln in nettlinjer), Decimal(0))
    andel_mnd = {}
    for mnd in (8, 9, 10):
        k = sum((ln["belop"] for ln in kasselinjer if ln["dato"].month == mnd), Decimal(0))
        n = sum((ln["belop"] for ln in nettlinjer if ln["dato"].month == mnd), Decimal(0))
        andel_mnd[f"2026-{mnd:02d}"] = {"kasse": tall(k), "nett": tall(n), "andel_nett": round(float(n / (k + n)), 4)}
    andel_uke = {}
    for u in sorted({uke(d) for d in DAGER}):
        k = sum((ln["belop"] for ln in kasselinjer if uke(ln["dato"]) == u), Decimal(0))
        n = sum((ln["belop"] for ln in nettlinjer if uke(ln["dato"]) == u), Decimal(0))
        andel_uke[u] = {"kasse": tall(k), "nett": tall(n), "andel_nett": round(float(n / (k + n)), 4)}
    nett_utc = [ln for ln in nettlinjer if ln["solgt"].date() != ln["dato"]]
    f["modul6_nett"] = {
        "slv__salgslinje_rader_kasse_og_nett": len(alle_linjer),
        "gld__f__salg_rader": len(alle_linjer),
        "nett_linjer": len(nettlinjer), "nett_ordrer": len({ln["salgsnummer"] for ln in nettlinjer}),
        "belop_totalt": tall(sum_kasse + sum_nett), "belop_nett": tall(sum_nett),
        "andel_nett_totalt": round(float(sum_nett / (sum_kasse + sum_nett)), 4),
        "andel_nett_per_maned": andel_mnd, "andel_nett_per_uke": andel_uke,
        "h13_nett": {"linjer_utc_dato_ulik_salgsdato": len(nett_utc),
                     "ordrer": len({ln["salgsnummer"] for ln in nett_utc})},
        "omsetning_uke_butikk_varegruppe_alle": omsetning(alle_linjer),
    }

    # ---- kunde (modul 7) ----
    def niva_paa(nr, d):
        m = medlem_nr.get(nr)
        return None if m is None else medlem_paa(m, d)["niva"]

    per_niva = defaultdict(lambda: [0, Decimal(0)])
    gull_naa = [0, Decimal(0)]
    for ln in alle_linjer:
        if ln["medlem"] is None:
            k = "-2"
        elif ln["medlem"] not in medlem_nr:
            k = "-1"
        else:
            k = niva_paa(ln["medlem"], ln["dato"])
            if medlem_paa(medlem_nr[ln["medlem"]], TIL)["niva"] == "GOLD":
                gull_naa[0] += 1
                gull_naa[1] += ln["belop"]
        per_niva[k][0] += 1
        per_niva[k][1] += ln["belop"]
    m42 = medlem_v[(M42,)]
    m42_linjer = [ln for ln in alle_linjer if ln["medlem"] == M42]
    uten_kort = sum(1 for kv in kvitteringer if kv["medlem"] is None)
    f["modul7_kunde"] = {
        "gld__d__kunde_rader_uten_minus": rader_bronze["brz__lojal__medlem"],
        "medlemmer_i_siste_uttrekk": len(medlem_v),
        "medlem_300042_versjoner": [{"tier": dict(v["verdier"])["niva"], "postalCode": dict(v["verdier"])["postnr"],
                                     "fra_uttrekk": v["fra"], "til_uttrekk": v["til"]} for v in m42],
        "medlem_300042_salg": [{"salgsdato": ln["dato"].isoformat(), "kanal": ln["kanal"], "salgsnummer": ln["salgsnummer"],
                                "linje": ln["linje"], "niva_paa_salgsdato": niva_paa(M42, ln["dato"]), "belop": tall(ln["belop"])}
                               for ln in sorted(m42_linjer, key=lambda x: (x["solgt"], x["linje"]))],
        "fk__gld__d__kunde": {"-2_linjer": per_niva["-2"][0], "-1_linjer": per_niva["-1"][0],
                      "-1_medlemsnummer": str(H15_MEDLEM), "-1_salgsdato": H15_DAG.isoformat()},
        "salg_per_niva_paa_salgsdato": {k: {"linjer": x[0], "belop": tall(x[1])} for k, x in sorted(per_niva.items())},
        "salg_fra_dagens_gull_medlemmer": {"linjer": gull_naa[0], "belop": tall(gull_naa[1]),
                                           "merknad": "medlemmer som er GOLD i siste uttrekk, uansett nivå da de handlet"},
        "kvitteringer_uten_medlemskort": {"antall": uten_kort, "av": len(kvitteringer),
                                          "andel": round(uten_kort / len(kvitteringer), 4)},
        "regel_niva_paa_salgsdato": "nivået i uttrekket kl. 04 samme dag (før butikkene åpner)",
    }

    # ---- lager (modul 11) ----
    fakta = 0
    per_butikk_dag = defaultdict(dict)
    tomme = []
    for d in DAGER:
        for b in FYSISKE:
            if b == LILLEHAMMER and d < LILLEHAMMER_APNER:
                continue
            sum_hand = sum_ordre = 0
            for nr in vare_nr:
                on_hand, on_order = lager_dag[(d, b, nr)]
                if d.weekday() == 6:
                    assert (on_hand, on_order) == lager_dag[(d - timedelta(days=1), b, nr)]  # H16
                fakta += 1
                sum_hand += on_hand
                sum_ordre += on_order
                if on_hand == 0:
                    tomme.append({"dato": d.isoformat(), "butikk": b, "varenummer": str(nr), "uke": uke(d)})
            per_butikk_dag[d.isoformat()][str(b)] = {"antall_pa_lager": sum_hand, "antall_i_bestilling": sum_ordre}
    serie_4711 = {d.isoformat(): {str(b): lager_dag[(d, b, 4711)][0] for b in FYSISKE
                                  if not (b == LILLEHAMMER and d < LILLEHAMMER_APNER)} for d in DAGER}
    serie_h17 = {d.isoformat(): {"antall_pa_lager": lager_dag[(d, H17_BUTIKK, h17)][0],
                                 "antall_i_bestilling": lager_dag[(d, H17_BUTIKK, h17)][1]}
                 for d in DAGER if date(2026, 9, 26) <= d <= date(2026, 10, 6)}
    f["modul11_lager"] = {
        "gld__f__lagerbeholdning_rader": fakta,
        "regel": "én rad per vare, butikk og dag fra butikkens første telling; søndag = lørdagens telling (H16)",
        "tellingsdager": sum(1 for d in DAGER if er_tellingsdag(d)),
        "varer_tomme": tomme,
        "h17": {"butikk": H17_BUTIKK, "varenummer": str(h17), "serie": serie_h17},
        "sum_per_dag_og_butikk": dict(per_butikk_dag),
        "vare_4711_antall_pa_lager": serie_4711,
    }

    # ---- hendelsene ----
    f["hendelser"] = {
        "H1": "varenummer med ledende nuller i varesystemet og nettbutikken (004711), uten i kassen og lageret (4711)",
        "H2": "varesystemet: desimalkomma og dd.MM.yyyy",
        "H3": f"004711 UTPRIS 1299,00 -> {kr_komma(H3_NY_PRIS)} i uttrekket {H3_FRA.isoformat()}",
        "H4": f"{h4_nr:06d} ({VARE_H4[0]}) {VARE_H4[1]} -> {VARE_H4[2]} i uttrekket {H4_FRA.isoformat()}",
        "H5": f"106 i aktor fra uttrekket {LILLEHAMMER_I_VARESYSTEM.isoformat()}, AAPNET_DT 05.09.2026, salg fra {LILLEHAMMER_APNER}",
        "H6": f"{h6:06d} ({VARE_H6}) STATUS U i uttrekket {H6_FRA.isoformat()}",
        "H7": f"{uten_kort} av {len(kvitteringer)} kvitteringer uten memberNo",
        "H8": f"{H8_LINJER} linjer med sku 9999 på salgsdato {H8_DAG}",
        "H9": f"{len(retur)} returlinjer (negativ qty)",
        "H10": f"campaignCode i kvitteringslinje fra salgsdato {H10_FRA} (filen {kasse_ankomst(H10_FRA).isoformat()})",
        "H11": f"én linje to ganger i {h11_fil}",
        "H12": f"filene for {SEN_DAG} kom {SEN_ANKOMST.isoformat()} (ingen kassefil 2026-09-13T06:00)",
        "H13": f"{len(utc_annen_dato_kv)} kvitteringer og {f['modul6_nett']['h13_nett']['ordrer']} nettordrer med UTC-dato dagen før norsk dato",
        "H14": f"300042 SILVER -> GOLD i uttrekket {H14_GULL}, postnummer 0367 -> {H14_NYTT_POSTNR} i uttrekket {H14_FLYTTER}",
        "H15": f"nettordre fra {H15_MEDLEM} (ikke i kundeklubben) på salgsdato {H15_DAG}",
        "H16": "ingen lagerfil på søndager",
        "H17": f"vare {h17:06d} tom i butikk {H17_BUTIKK} fra {H17_TOM} til {H17_LEVERT} (uke 40)",
    }
    return f


def skriv_fasit_md(rot, f):
    m2, m3, m4, m5, m6, m7, m11 = (f[k] for k in ["modul2_raw", "modul3_bronze", "modul4_solv", "modul5_gull_salg",
                                                   "modul6_nett", "modul7_kunde", "modul11_lager"])

    def nok(x):
        return f"{x:,.2f}".replace(",", " ").replace(".", ",")

    def pst(x):
        return f"{x * 100:.1f} %".replace(".", ",")

    l = ["# Fasit for kursdataene", "",
         "Generert av `tools/lag_data.py`. Ikke rediger for hånd. Alle tall står i `fasit/fasit.json`.", "",
         "Tallene er regnet av programmet som lager dataene, ikke lest fra filene og ikke fra pipelinen. "
         "Salgsdato er norsk dato "
         "(Europe/Oslo) av `soldAt`/`ordered_at`. `belop = antall * enhetspris - rabatt`, kroner med mva. "
         "Nettprisen er etter rabatt, så rabatten er 0 for nettbutikken.", "",
         f"Periode {f['om']['periode'][0]} til {f['om']['periode'][1]}. {f['filer']['antall']} filer i landing.", "",
         "## Modul 2: raw", "", "| Tabell | Filer | Rader |", "|---|---|---|"]
    for t_, x in m2["rader_per_tabell"].items():
        l.append(f"| `{t_}` | {x['filer']} | {x['rader']} |")
    l += ["", "## Modul 3: bronze", "", "| Tabell | Rader (alle versjoner) |", "|---|---|"]
    for t_, x in m3["rader_per_tabell"].items():
        l.append(f"| `{t_}` | {x} |")
    l += ["", f"- `004711` har {len(m3['vare_004711_versjoner'])} versjoner: UTPRIS "
          + " og ".join(f"{nok(v['UTPRIS'])}" for v in m3["vare_004711_versjoner"]) + ".",
          f"- Kvitteringslinjen har {m3['kvitteringslinje_raw_minus_bronze']} rad mer i raw enn i bronze.", "",
          "## Modul 4: sølv", "",
          f"- `slv__salgslinje` (kassen): {m4['slv__salgslinje_rader_kasse']} rader.",
          f"- `fb__slv__produkt` uten treff: {m4['fb__slv__produkt_uten_treff']['linjer']} linjer med varenummer 9999.",
          f"- Lillehammer: første salgsdato {m4['lillehammer']['forste_salgsdato']}, første `soldAt` "
          f"{m4['lillehammer']['forste_solgt_tidspunkt_utc']}.",
          f"- Salgsdato 2026-09-12: {m4['h12_salgsdato_2026_09_12']['linjer']} linjer, i filen som kom 14. september.",
          f"- {m4['h13_kasse']['kvitteringer']} kvitteringer har UTC-dato dagen før salgsdatoen.", "",
          "## Modul 5: første stjerne", "",
          f"- `gld__f__salg` (kassen): {m5['gld__f__salg_rader_kasse']} rader, `fk__gld__d__produkt = -1` på {m5['fk__gld__d__produkt']['-1']}.",
          f"- Omsetning i kassen: {nok(m5['belop_totalt_kasse'])} kr.",
          f"- Returer: {m5['retur']['linjer']} linjer ({pst(m5['retur']['andel_av_kasselinjer'])}), "
          f"{nok(m5['retur']['belop_sum'])} kr.", "",
          "| Butikk | Omsetning kasse |", "|---|---|"]
    for b, x in m5["belop_per_butikk_kasse"].items():
        l.append(f"| {b} | {nok(x)} |")
    l += ["", "Omsetning per butikk, varegruppe og ISO-uke: `modul5_gull_salg.omsetning_uke_butikk_varegruppe_kasse` "
          "(varegruppe etter SCD1, altså siste uttrekk).", "",
          "## Modul 6: nettbutikken", "",
          f"- `slv__salgslinje` med nett: {m6['slv__salgslinje_rader_kasse_og_nett']} rader.",
          f"- Nettandel av omsetningen: {pst(m6['andel_nett_totalt'])} totalt; "
          + ", ".join(f"{k}: {pst(v['andel_nett'])}" for k, v in m6["andel_nett_per_maned"].items()) + ".", "",
          "## Modul 7: kunden", "",
          f"- `300042` har {len(m7['medlem_300042_versjoner'])} versjoner: "
          + ", ".join(f"{v['tier']}/{v['postalCode']} fra {v['fra_uttrekk'][:10]}" for v in m7["medlem_300042_versjoner"]) + ".",
          f"- `fk__gld__d__kunde = -2` på {m7['fk__gld__d__kunde']['-2_linjer']} linjer (uten kort), `-1` på {m7['fk__gld__d__kunde']['-1_linjer']} "
          f"(medlem {m7['fk__gld__d__kunde']['-1_medlemsnummer']}).",
          f"- Kvitteringer uten medlemskort: {pst(m7['kvitteringer_uten_medlemskort']['andel'])}.",
          "- Nivå på salgsdato = nivået i uttrekket kl. 04 samme dag.", "",
          "| Nivå på salgsdato | Linjer | Beløp |", "|---|---|---|"]
    for k, x in m7["salg_per_niva_paa_salgsdato"].items():
        l.append(f"| {k} | {x['linjer']} | {nok(x['belop'])} |")
    l += ["", "## Modul 11: lager", "",
          f"- `gld__f__lagerbeholdning`: {m11['gld__f__lagerbeholdning_rader']} rader (søndag = lørdagens telling).",
          "- Tomme varer: " + ", ".join(f"{x['varenummer']} i {x['butikk']} {x['dato']}" for x in m11["varer_tomme"]) + ".", ""]
    with open(os.path.join(rot, "docs", "fasit.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(l))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--rot", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = p.parse_args()
    varer = lag_varer()
    medlemmer = lag_medlemmer()
    kalender = lag_kalender()
    kvitteringer, kasselinjer, nettlinjer, lager_dag, h17, h6 = simuler(varer, medlemmer)
    filer = lag_filer(varer, medlemmer, kvitteringer, kasselinjer, nettlinjer, lager_dag, kalender)
    data = os.path.join(a.rot, "data")
    if os.path.isdir(data):
        import shutil
        shutil.rmtree(data)
    skriv_landing(a.rot, filer)
    fasit = lag_fasit(varer, medlemmer, kvitteringer, kasselinjer, nettlinjer, lager_dag, kalender, filer, h17, h6)
    os.makedirs(os.path.join(a.rot, "fasit"), exist_ok=True)
    os.makedirs(os.path.join(a.rot, "docs"), exist_ok=True)
    with open(os.path.join(a.rot, "fasit", "fasit.json"), "w", encoding="utf-8") as fh:
        json.dump(fasit, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    skriv_fasit_md(a.rot, fasit)
    print(f"{len(filer)} filer i {data}/landing, fasit i fasit/fasit.json og docs/fasit.md")


if __name__ == "__main__":
    main()
