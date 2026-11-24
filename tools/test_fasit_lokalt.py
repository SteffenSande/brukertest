#!/usr/bin/env python3
"""Fasittesten for modul 2-7 og 11, lokalt: bygger de genererte tabellene med lokal Spark over alle
leveransene i data/landing (tester/pyspark/kjor_lokalt.py) og sammenligner med fasit/fasit.json.

  JAVA_HOME=/opt/homebrew/opt/openjdk@17 uv run --no-project --with pyspark --with pyyaml python tools/test_fasit_lokalt.py
  uv run --no-project --with pyyaml python tools/test_fasit_lokalt.py --databricks       mot tabellene i Databricks
  ... --modul 3     bare sjekkene for modul 2 til og med 3 (./kurs sjekk M3 bruker det)

Hvilken modul en tabell hører til, står i tools/kursmoduler.py. Kalenderen hører til modul 5, så
sjekkene for raw__kalender__dag og brz__kalender__dag står under modul 5. Mangler en tabell modulen trenger,
teller det som én feil per tabell, og resten av sjekkene for den modulen hoppes over. Fra modul 6 har salgslinjen og
faktaen også nettbutikken. Sjekkene for modul 4 og 5 gjelder kassen (sys__kildesystem = 'kassio'), så de er like
før og etter modul 6.

Fasiten er regnet fra generatorens sannhet (tools/lag_data.py), ikke fra pipelinen. Testen leser bare tabellene;
den regner ingen pipelinelogikk selv utover spørringene som svarer på spørsmålene i modulene.
Avslutter med kode 1 hvis noe avviker.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tester", "pyspark"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from kursmoduler import TABELLER_PER_MODUL, tabeller_til_og_med  # noqa: E402

FASIT = json.load(open(os.path.join(ROOT, "fasit", "fasit.json"), encoding="utf-8"))
APEN = "9999-12-31 00:00:00"
KASSE = "sys__kildesystem = 'kassio'"

RESULTAT = {"ok": 0, "feil": 0}


def sjekk(navn, faktisk, forventet):
    ok = faktisk == forventet
    RESULTAT["ok" if ok else "feil"] += 1
    if ok:
        print(f"  ok   {navn}: {kort(faktisk)}")
    else:
        print(f"  FEIL {navn}\n         forventet: {kort(forventet, 600)}\n         faktisk:   {kort(faktisk, 600)}")


def kort(v, n=120):
    s = json.dumps(v, ensure_ascii=False, default=str, sort_keys=True) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + " …"


def r2(x):
    return None if x is None else round(float(x), 2)


def databricks_sql(profil, katalog, skjema):
    """Kjører spørringer mot tabellene i Databricks (SQL Statement API via Databricks CLI-profilen) og
    gjør verdiene om til de samme Python-typene som lokal Spark gir. Ingen token leses eller skrives ut."""
    import datetime
    import decimal
    import subprocess
    import time

    lager = json.loads(subprocess.run(["databricks", "warehouses", "list", "-p", profil, "-o", "json"],
                                      check=True, capture_output=True, text=True).stdout)
    if not lager:
        sys.exit("Fant ingen SQL warehouse i arbeidsflaten.")
    warehouse = lager[0]["id"]

    def api(metode, sti, body=None):
        cmd = ["databricks", "api", metode, sti, "-p", profil]
        if body is not None:
            cmd += ["--json", json.dumps(body)]
        return json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)

    def verdi(v, typ):
        if v is None:
            return None
        if typ.startswith("ARRAY<"):
            indre = typ[6:-1]
            return [verdi(e if isinstance(e, str) or e is None else str(e), indre) for e in json.loads(v)]
        if typ in ("INT", "LONG", "SHORT", "BYTE"):
            return int(v)
        if typ == "DECIMAL":
            return decimal.Decimal(v)
        if typ in ("DOUBLE", "FLOAT"):
            return float(v)
        if typ == "BOOLEAN":
            return v == "true"
        if typ == "DATE":
            return datetime.date.fromisoformat(v)
        if typ == "TIMESTAMP":
            return datetime.datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        return v

    def sql(q):
        svar = api("post", "/api/2.0/sql/statements", {
            "statement": q, "warehouse_id": warehouse, "catalog": katalog, "schema": skjema,
            "wait_timeout": "50s", "disposition": "INLINE", "format": "JSON_ARRAY"})
        while svar["status"]["state"] in ("PENDING", "RUNNING"):
            time.sleep(2)
            svar = api("get", f"/api/2.0/sql/statements/{svar['statement_id']}")
        if svar["status"]["state"] != "SUCCEEDED":
            raise RuntimeError(f"Spørringen feilet: {svar['status']}\n{q}")
        kolonner = svar.get("manifest", {}).get("schema", {}).get("columns") or []  # DDL gir ingen kolonner
        typer = [k["type_text"].upper() if k["type_name"] == "ARRAY" else k["type_name"] for k in kolonner]
        rader = list(svar.get("result", {}).get("data_array") or [])
        neste = svar.get("result", {}).get("next_chunk_internal_link")
        while neste:
            del_ = api("get", neste)
            rader += del_.get("data_array") or []
            neste = del_.get("next_chunk_internal_link")
        return [tuple(verdi(v, t) for v, t in zip(r, typer)) for r in rader]

    return sql


def modul_fra_argumenter():
    if "--modul" not in sys.argv:
        return max(TABELLER_PER_MODUL)
    m = int(sys.argv[sys.argv.index("--modul") + 1].lstrip("Mm"))
    if not min(TABELLER_PER_MODUL) <= m <= max(TABELLER_PER_MODUL):
        sys.exit(f"--modul må være fra {min(TABELLER_PER_MODUL)} til {max(TABELLER_PER_MODUL)} (modul 8-10 sjekker det samme som 7)")
    return m


def main():
    til_modul = modul_fra_argumenter()
    if "--databricks" in sys.argv:
        profil = os.environ.get("DATABRICKS_PROFILE", "kurs")
        sql = databricks_sql(profil, os.environ.get("KATALOG", "workspace"), os.environ.get("SKJEMA", "toppfart"))
        print(f"Leser tabellene i Databricks (profil {profil})")
    else:
        from kjor_lokalt import bygg
        spark = bygg(vis=lambda s: None if s.startswith("  ok") else print(s))

        def sql(q):
            return [tuple(r) for r in spark.sql(q).collect()]

    kjor_sjekker(sql, til_modul)
    print(f"Fasittest (modul 2-{til_modul}): {RESULTAT['ok']} riktige, {RESULTAT['feil']} feil.")
    sys.exit(1 if RESULTAT["feil"] else 0)


def kjor_sjekker(sql, til_modul):
    """Alle sjekkene for modul 2 til og med til_modul. `sql(spørring)` gir radene som tupler. Brukes også av
    notebooks/kurs_sjekk.py med spark.sql. Tellingen står i RESULTAT."""
    def en(q):
        return sql(q)[0][0]

    finnes = {r[1] for r in sql("SHOW TABLES")}

    def modul(m, tittel):
        """Skriver overskriften og sier om modulens sjekker skal kjøres: modulen er med i --modul, og alle
        tabellene modulen sjekker finnes."""
        if m > til_modul:
            return False
        print(f"Modul {m}: {tittel}")
        mangler = [t for t in tabeller_til_og_med(m) if t not in finnes]
        for t in mangler:
            RESULTAT["feil"] += 1
            print(f"  FEIL tabellen {t} finnes ikke i Databricks")
        if mangler:
            print(f"  (resten av sjekkene for modul {m} hoppes over til tabellene finnes)")
        return not mangler

    per_fil = FASIT["filer"]["per_fil"]
    kilde = {k: k for k in ("varius", "kassio", "kalender", "nettora", "lojal", "lagra")}

    def raw_sjekker(tabeller):
        m2 = FASIT["modul2_raw"]["rader_per_tabell"]
        for t in tabeller:
            sjekk(f"{t} rader", en(f"SELECT count(*) FROM {t}"), m2[t]["rader"])
            objekt = t.split("__")[2]
            filer = {p: n for p, n in per_fil.items() if p.split("/")[-2] == objekt and p.split("/")[-1].startswith(objekt + "_")}
            sjekk(f"{t} filer i landing", len(filer), m2[t]["filer"])
            faktisk = {re.sub(r"^.*?/landing/", "data/landing/", p): n for p, n in sql(f"SELECT sys__kildefil, count(*) FROM {t} GROUP BY 1")}
            sjekk(f"{t} rader per fil (filer uten rader har ingen rad)", faktisk, {p: n for p, n in filer.items() if n > 0})
        sjekk(f"sys__kildesystem i {', '.join(tabeller)}",
              sorted(sql(" UNION ".join(f"SELECT DISTINCT '{t}', sys__kildesystem FROM {t}" for t in tabeller))),
              sorted((t, kilde[t.split("__")[1]]) for t in tabeller))

    def brz_rader(tabeller):
        for t in tabeller:
            sjekk(f"{t} rader (alle versjoner)", en(f"SELECT count(*) FROM {t}"), FASIT["modul3_bronze"]["rader_per_tabell"][t])

    # ------------------------------------------------------------------ modul 2: raw
    if modul(2, "raw"):
        modul2(raw_sjekker)
    # ------------------------------------------------------------------ modul 3: bronze
    if modul(3, "bronze"):
        modul3(sql, en, brz_rader)
    # ------------------------------------------------------------------ modul 4: sølv
    if modul(4, "sølv"):
        modul4(sql, en)
    # ------------------------------------------------------------------ modul 5: kalender og første stjerne
    if modul(5, "kalender og første stjerne"):
        raw_sjekker(["raw__kalender__dag"])
        brz_rader(["brz__kalender__dag"])
        sjekk("HELLIGDAG som sann/usann, ingen tomme", en("SELECT count(*) FROM brz__kalender__dag WHERE HELLIGDAG IS NULL"), 0)
        modul5(sql, en)
    # ------------------------------------------------------------------ modul 6: nettbutikken (union i sølv)
    if modul(6, "nettbutikken"):
        raw_sjekker(["raw__nettora__ordrelinje"])
        brz_rader(["brz__nettora__ordrelinje"])
        modul6(sql, en)
    # ------------------------------------------------------------------ modul 7: kunden og historikk (SCD2)
    if modul(7, "kunden og historikk"):
        raw_sjekker(["raw__lojal__medlem"])
        brz_rader(["brz__lojal__medlem"])
        modul7(sql, en)
    # ------------------------------------------------------------------ modul 11: lagerbeholdning (øyeblikksbilde)
    if modul(11, "lagerbeholdning"):
        raw_sjekker(["raw__lagra__beholdning"])
        brz_rader(["brz__lagra__beholdning"])
        modul11(sql, en)


def modul2(raw_sjekker):
    raw_sjekker([t for t in TABELLER_PER_MODUL[2] if t.startswith("raw__")])


def modul3(sql, en, brz_rader):
    m3 = FASIT["modul3_bronze"]
    brz_rader([t for t in TABELLER_PER_MODUL[3] if t.startswith("brz__")])
    for t in ("brz__varius__vare", "brz__varius__aktor"):
        sjekk(f"{t} gjeldende rader", en(f"SELECT count(*) FROM {t} WHERE sys__gyldig_til = TIMESTAMP'{APEN}'"), m3["gjeldende_rader"][t])
    versjoner = sql("SELECT UTPRIS, sys__gyldig_fra, sys__gyldig_til FROM brz__varius__vare WHERE VARENR = '4711' ORDER BY sys__gyldig_fra")
    sjekk("004711 har to versjoner med UTPRIS og gyldighet",
          [(r2(p), str(f), str(t)) for p, f, t in versjoner],
          [(r2(v["UTPRIS"]), v["fra_uttrekk"].replace("T", " "), (v["til_uttrekk"] or APEN).replace("T", " "))
           for v in m3["vare_004711_versjoner"]])
    sjekk("varer med flere versjoner", dict(sql("SELECT VARENR, count(*) FROM brz__varius__vare GROUP BY 1 HAVING count(*) > 1")),
          {k.lstrip("0"): v for k, v in m3["varer_med_flere_versjoner"].items()})
    sjekk("kvitteringslinje: raw minus bronze (samme linje to ganger i én fil)",
          en("SELECT count(*) FROM raw__kassio__kvitteringslinje") - en("SELECT count(*) FROM brz__kassio__kvitteringslinje"),
          m3["kvitteringslinje_raw_minus_bronze"])
    sjekk("VARENR uten ledende nuller", en("SELECT count(*) FROM brz__varius__vare WHERE VARENR LIKE '0%'"), 0)
    sjekk("UTPRIS som tall, ingen tomme", en("SELECT count(*) FROM brz__varius__vare WHERE UTPRIS IS NULL"), 0)
    sjekk("AAPNET_DT for Lillehammer som dato", str(en("SELECT AAPNET_DT FROM brz__varius__aktor WHERE AKTNR = 106")), "2026-09-05")
    sjekk("soldAt som tidspunkt, ingen tomme", en("SELECT count(*) FROM brz__kassio__kvittering WHERE soldAt IS NULL"), 0)


def modul4(sql, en):
    m4 = FASIT["modul4_solv"]
    gj = f"sys__gyldig_til = TIMESTAMP'{APEN}'"
    # Fra modul 6 har salgslinjen også nettbutikken. Tallene for modul 4 gjelder kassen.
    sl = f"(SELECT * FROM slv__salgslinje WHERE {KASSE})"
    sjekk("slv__salgslinje rader (kassen)", en(f"SELECT count(*) FROM {sl} WHERE {gj}"), m4["slv__salgslinje_rader_kasse"])
    for t, nokkel in (("slv__butikk", "slv__butikk_rader"), ("slv__leverandor", "slv__leverandor_rader"),
                      ("slv__produkt", "slv__produkt_rader"), ("slv__produktgruppe", "slv__produktgruppe_rader")):
        sjekk(f"{t} gjeldende rader", en(f"SELECT count(*) FROM {t} WHERE {gj}"), m4[nokkel])
    uten = sql(f"""SELECT count(*), collect_set(s.varenummer), collect_set(cast(s.salg_dato AS string)) FROM {sl} s
                  LEFT JOIN slv__produkt p ON p.bk__slv__produkt = s.fb__slv__produkt WHERE p.bk__slv__produkt IS NULL""")[0]
    f = m4["fb__slv__produkt_uten_treff"]
    sjekk("fb__slv__produkt uten treff", [uten[0], sorted(uten[1]), sorted(uten[2])], [f["linjer"], [f["varenummer"]], [f["salgsdato"]]])
    sjekk("fb__slv__butikk treffer alltid", en(f"""SELECT count(*) FROM {sl} s LEFT JOIN slv__butikk b
                                                 ON b.bk__slv__butikk = s.fb__slv__butikk WHERE b.bk__slv__butikk IS NULL"""), 0)
    lh = sql(f"SELECT cast(min(salg_dato) AS string), date_format(min(salg_tidspunkt), \"yyyy-MM-dd'T'HH:mm:ss'Z'\"), count(*) FROM {sl} WHERE butikknummer = 106")[0]
    sjekk("Lillehammer: første salgsdato, første tidspunkt (UTC), linjer", list(lh),
          [m4["lillehammer"]["forste_salgsdato"], m4["lillehammer"]["forste_solgt_tidspunkt_utc"], m4["lillehammer"]["linjer"]])
    h12 = m4["h12_salgsdato_2026_09_12"]
    filtid = re.search(r"_(\d{8})T(\d{2})(\d{2})", h12["fil"]).groups()
    filtid = f"{filtid[0][:4]}-{filtid[0][4:6]}-{filtid[0][6:]} {filtid[1]}:{filtid[2]}:00"
    sjekk("salgsdato 2026-09-12: linjer, og alle kom med filen 14. september",
          sql(f"SELECT count(*), collect_set(cast(sys__gyldig_fra AS string)) FROM {sl} WHERE salg_dato = DATE'2026-09-12'")[0][:2],
          (h12["linjer"], [filtid]))
    h13 = m4["h13_kasse"]
    ulik = "to_date(salg_tidspunkt) <> salg_dato"
    sjekk("UTC-dato ulik norsk salgsdato: linjer", en(f"SELECT count(*) FROM {sl} WHERE {ulik}"), h13["linjer_utc_dato_ulik_salgsdato"])
    sjekk("UTC-dato ulik norsk salgsdato: kvitteringer",
          en(f"SELECT count(DISTINCT butikknummer, salgsnummer) FROM {sl} WHERE {ulik}"), h13["kvitteringer"])
    sjekk("UTC-dato ulik norsk salgsdato: linjer per salgsdato",
          dict(sql(f"SELECT cast(salg_dato AS string), count(*) FROM {sl} WHERE {ulik} GROUP BY 1")), h13["per_salgsdato"])
    faktisk = {}
    for d, b, n, s in sql(f"SELECT cast(salg_dato AS string), cast(butikknummer AS string), count(*), sum(belop) FROM {sl} GROUP BY 1, 2"):
        faktisk.setdefault(d, {})[b] = {"linjer": n, "belop": r2(s)}
    forventet = {d: {b: {"linjer": v["linjer"], "belop": r2(v["belop"])} for b, v in bs.items()} for d, bs in m4["salgslinjer_per_butikk_per_dato"].items()}
    avvik = sorted(d for d in set(faktisk) | set(forventet) if faktisk.get(d) != forventet.get(d))
    sjekk(f"linjer og beløp per butikk og salgsdato ({len(forventet)} datoer)", avvik, [])


def modul5(sql, en):
    m5 = FASIT["modul5_gull_salg"]
    # Fra modul 6 har faktaen også nettbutikken. Tallene for modul 5 gjelder kassen.
    fs = f"(SELECT * FROM gld__f__salg WHERE {KASSE})"
    sjekk("gld__f__salg rader (kassen)", en(f"SELECT count(*) FROM {fs}"), m5["gld__f__salg_rader_kasse"])
    sjekk("gld__f__salg pk__ er unik", en(f"SELECT count(DISTINCT pk__gld__f__salg) FROM {fs}"), m5["gld__f__salg_rader_kasse"])
    sjekk("gld__d__produkt rader uten -1 og -2", en("SELECT count(*) FROM gld__d__produkt WHERE pk__gld__d__produkt NOT IN (-1, -2)"), m5["gld__d__produkt_rader_uten_minus"])
    sjekk("gld__d__butikk rader uten -1 og -2", en("SELECT count(*) FROM gld__d__butikk WHERE pk__gld__d__butikk NOT IN (-1, -2)"), m5["gld__d__butikk_rader_uten_minus"])
    for d in ("gld__d__produkt", "gld__d__butikk", "gld__d__dato"):
        sjekk(f"{d} har spesialradene -1 Ukjent og -2 Mangler",
              sql(f"SELECT pk__{d}, bk__{d} FROM {d} WHERE pk__{d} IN (-1, -2) ORDER BY 1"), [(-2, -2), (-1, -1)])
    sjekk("gld__d__dato: pk__ er datoen som ÅÅÅÅMMDD",
          en("SELECT count(*) FROM gld__d__dato WHERE pk__gld__d__dato NOT IN (-1, -2) AND pk__gld__d__dato <> cast(date_format(dato, 'yyyyMMdd') AS bigint)"), 0)
    sjekk("gld__d__dato: 2026-08-01 har pk__ 20260801", en("SELECT pk__gld__d__dato FROM gld__d__dato WHERE dato = DATE'2026-08-01'"), 20260801)
    sjekk("fk__gld__d__produkt = -1 og -2",
          dict(sql(f"SELECT cast(fk__gld__d__produkt AS string), count(*) FROM {fs} WHERE fk__gld__d__produkt IN (-1, -2) GROUP BY 1")),
          {k: v for k, v in m5["fk__gld__d__produkt"].items() if v})
    sjekk("fk__gld__d__butikk og fk__gld__d__dato treffer alltid",
          en(f"SELECT count(*) FROM {fs} WHERE fk__gld__d__butikk IN (-1, -2) OR fk__gld__d__dato IN (-1, -2)"), 0)
    sjekk("omsetning i kassen", r2(en(f"SELECT sum(belop) FROM {fs}")), r2(m5["belop_totalt_kasse"]))
    stjerne = f"""{fs} f JOIN gld__d__butikk b ON b.pk__gld__d__butikk = f.fk__gld__d__butikk
                 JOIN gld__d__produkt p ON p.pk__gld__d__produkt = f.fk__gld__d__produkt
                 JOIN gld__d__dato d ON d.pk__gld__d__dato = f.fk__gld__d__dato"""
    sjekk("omsetning per butikk", {b: r2(s) for b, s in sql(f"SELECT cast(b.butikknummer AS string), sum(f.belop) FROM {stjerne} GROUP BY 1")},
          {b: r2(s) for b, s in m5["belop_per_butikk_kasse"].items()})
    gruppe = "CASE WHEN p.pk__gld__d__produkt = -1 THEN '-1' ELSE p.produktgruppekode END"
    sjekk("omsetning per varegruppe, SCD1", {g: r2(s) for g, s in sql(f"SELECT {gruppe}, sum(f.belop) FROM {stjerne} GROUP BY 1")},
          {g: r2(s) for g, s in m5["belop_per_varegruppe_kasse_scd1"].items()})
    sjekk("varegruppenavn i produktdimensjonen", dict(sql("SELECT DISTINCT produktgruppekode, produktgruppenavn FROM gld__d__produkt WHERE pk__gld__d__produkt NOT IN (-1, -2)")),
          {k: v for k, v in m5["varegruppenavn"].items() if k != "-1"})
    retur = m5["retur"]
    rl = sql(f"SELECT count(*), sum(antall), sum(belop) FROM {fs} WHERE antall < 0")[0]
    sjekk("returer: linjer, antall, beløp", [rl[0], rl[1], r2(rl[2])], [retur["linjer"], retur["antall_sum"], r2(retur["belop_sum"])])
    sjekk("returer: andel av linjene", round(rl[0] / en(f"SELECT count(*) FROM {fs}"), 4), retur["andel_av_kasselinjer"])
    sjekk("returer per butikk",
          {b: {"linjer": n, "antall": a, "belop": r2(s)} for b, n, a, s in
           sql(f"SELECT cast(b.butikknummer AS string), count(*), sum(f.antall), sum(f.belop) FROM {stjerne} WHERE f.antall < 0 GROUP BY 1")},
          {b: {"linjer": v["linjer"], "antall": v["antall"], "belop": r2(v["belop"])} for b, v in retur["per_butikk"].items()})
    h3 = m5["h3_004711"]
    sjekk("004711 i produktdimensjonen har den nye prisen, SCD1", r2(en("SELECT utpris_belop FROM gld__d__produkt WHERE varenummer = '4711'")), r2(h3["gld__d__produkt_utpris_scd1"]))
    sjekk("004711: salgslinjer før og fra 1. oktober",
          list(sql(f"""SELECT sum(CASE WHEN d.dato < DATE'2026-10-01' THEN 1 ELSE 0 END), sum(CASE WHEN d.dato >= DATE'2026-10-01' THEN 1 ELSE 0 END)
                      FROM {stjerne} WHERE p.varenummer = '4711'""")[0]),
          [h3["salgslinjer_kasse_foer_okt"], h3["salgslinjer_kasse_fra_okt"]])
    h4 = m5["h4_gruppebytte"]
    sjekk("003178 står i den nye varegruppen i dimensjonen, SCD1", en(f"SELECT produktgruppekode FROM gld__d__produkt WHERE varenummer = '{h4['varenummer']}'"), h4["til"])
    h6 = m5["h6_utgatt"]
    sjekk("006652 er utgått (er_aktiv usann), men salget står",
          list(sql(f"""SELECT p.er_aktiv, count(*) > 0 FROM {stjerne} WHERE p.varenummer = '{h6['varenummer']}' GROUP BY 1""")[0]),
          [h6["er_aktiv"], True])
    faktisk = {}
    for u, b, g, s in sql(f"""SELECT concat(d.ar, '-W', lpad(cast(d.uke AS string), 2, '0')), cast(b.butikknummer AS string), {gruppe}, sum(f.belop)
                             FROM {stjerne} GROUP BY 1, 2, 3"""):
        faktisk.setdefault(u, {}).setdefault(b, {})[g] = r2(s)
    forventet = {u: {b: {g: r2(s) for g, s in gs.items()} for b, gs in bs.items()} for u, bs in m5["omsetning_uke_butikk_varegruppe_kasse"].items()}
    avvik = sorted(f"{u} {b} {g}: {faktisk.get(u, {}).get(b, {}).get(g)} mot {forventet.get(u, {}).get(b, {}).get(g)}"
                   for u in set(faktisk) | set(forventet) for b in set(faktisk.get(u, {})) | set(forventet.get(u, {}))
                   for g in set(faktisk.get(u, {}).get(b, {})) | set(forventet.get(u, {}).get(b, {}))
                   if faktisk.get(u, {}).get(b, {}).get(g) != forventet.get(u, {}).get(b, {}).get(g))
    celler = sum(len(gs) for bs in forventet.values() for gs in bs.values())
    sjekk(f"omsetning per butikk, varegruppe og ISO-uke ({celler} celler)", avvik, [])


STJERNE = """gld__f__salg f JOIN gld__d__butikk b ON b.pk__gld__d__butikk = f.fk__gld__d__butikk
             JOIN gld__d__produkt p ON p.pk__gld__d__produkt = f.fk__gld__d__produkt
             JOIN gld__d__dato d ON d.pk__gld__d__dato = f.fk__gld__d__dato"""
NETT = "b.butikknummer = 107"


def andeler(rader):
    """{periode: {kasse, nett, andel_nett}} fra (periode, kasse, nett)."""
    return {p: {"kasse": r2(k), "nett": r2(n), "andel_nett": round(float(n) / (float(k) + float(n)), 4)} for p, k, n in rader}


def modul6(sql, en):
    m6 = FASIT["modul6_nett"]
    gj = f"sys__gyldig_til = TIMESTAMP'{APEN}'"
    sjekk("slv__salgslinje rader (kasse og nett)", en(f"SELECT count(*) FROM slv__salgslinje WHERE {gj}"), m6["slv__salgslinje_rader_kasse_og_nett"])
    sjekk("nettbutikken: linjer og ordrer", list(sql("SELECT count(*), count(DISTINCT salgsnummer) FROM slv__salgslinje WHERE salgskanal = 'Nett'")[0]),
          [m6["nett_linjer"], m6["nett_ordrer"]])
    sjekk("nettbutikken etter unionen: butikknummer, rabatt, kildesystem",
          [sorted(x) if isinstance(x, list) else r2(x) for x in sql(
              "SELECT collect_set(butikknummer), sum(rabatt_belop), collect_set(sys__kildesystem) FROM slv__salgslinje WHERE salgskanal = 'Nett'")[0]],
          [[107], 0.0, ["nettora"]])
    sjekk("salgskanal per kildesystem", sorted(sql("SELECT DISTINCT sys__kildesystem, salgskanal FROM slv__salgslinje")),
          [("kassio", "Butikk"), ("nettora", "Nett")])
    sjekk("ingen tomme verdier i nøkler og beløp", en("""SELECT count(*) FROM slv__salgslinje WHERE butikknummer IS NULL OR salgsnummer IS NULL
                                                         OR linjenummer IS NULL OR rabatt_belop IS NULL OR belop IS NULL OR salg_dato IS NULL"""), 0)
    h13 = m6["h13_nett"]
    sjekk("nettbutikken: UTC-dato ulik norsk salgsdato, linjer og ordrer",
          list(sql("""SELECT count(*), count(DISTINCT salgsnummer) FROM slv__salgslinje
                      WHERE salgskanal = 'Nett' AND to_date(salg_tidspunkt) <> salg_dato""")[0]),
          [h13["linjer_utc_dato_ulik_salgsdato"], h13["ordrer"]])
    sjekk("gld__f__salg rader (kasse og nett)", en("SELECT count(*) FROM gld__f__salg"), m6["gld__f__salg_rader"])
    sjekk("gld__f__salg pk__ er unik", en("SELECT count(DISTINCT pk__gld__f__salg) FROM gld__f__salg"), m6["gld__f__salg_rader"])
    sjekk("fk__gld__d__butikk og fk__gld__d__dato treffer alltid, også for nettbutikken",
          en("SELECT count(*) FROM gld__f__salg WHERE fk__gld__d__butikk IN (-1, -2) OR fk__gld__d__dato IN (-1, -2)"), 0)
    tot = sql(f"SELECT sum(f.belop), sum(CASE WHEN {NETT} THEN f.belop END) FROM {STJERNE}")[0]
    sjekk("omsetning totalt og på nett", [r2(tot[0]), r2(tot[1])], [r2(m6["belop_totalt"]), r2(m6["belop_nett"])])
    sjekk("andel nett totalt", round(float(tot[1]) / float(tot[0]), 3), m6["andel_nett_totalt"])
    deler = f"sum(CASE WHEN NOT {NETT} THEN f.belop END), sum(CASE WHEN {NETT} THEN f.belop END)"
    sjekk("andel nett per måned", andeler(sql(f"SELECT concat(d.ar, '-', lpad(cast(d.maned AS string), 2, '0')), {deler} FROM {STJERNE} GROUP BY 1")),
          {p: {k: r2(v) if k != "andel_nett" else v for k, v in x.items()} for p, x in m6["andel_nett_per_maned"].items()})
    sjekk("andel nett per ISO-uke", andeler(sql(f"SELECT concat(d.ar, '-W', lpad(cast(d.uke AS string), 2, '0')), {deler} FROM {STJERNE} GROUP BY 1")),
          {p: {k: r2(v) if k != "andel_nett" else v for k, v in x.items()} for p, x in m6["andel_nett_per_uke"].items()})
    gruppe = "CASE WHEN p.pk__gld__d__produkt = -1 THEN '-1' ELSE p.produktgruppekode END"
    faktisk = {}
    for u, b, g, s in sql(f"""SELECT concat(d.ar, '-W', lpad(cast(d.uke AS string), 2, '0')), cast(b.butikknummer AS string), {gruppe}, sum(f.belop)
                             FROM {STJERNE} GROUP BY 1, 2, 3"""):
        faktisk.setdefault(u, {}).setdefault(b, {})[g] = r2(s)
    forventet = {u: {b: {g: r2(s) for g, s in gs.items()} for b, gs in bs.items()} for u, bs in m6["omsetning_uke_butikk_varegruppe_alle"].items()}
    avvik = sorted(f"{u} {b} {g}: {faktisk.get(u, {}).get(b, {}).get(g)} mot {forventet.get(u, {}).get(b, {}).get(g)}"
                   for u in set(faktisk) | set(forventet) for b in set(faktisk.get(u, {})) | set(forventet.get(u, {}))
                   for g in set(faktisk.get(u, {}).get(b, {})) | set(forventet.get(u, {}).get(b, {}))
                   if faktisk.get(u, {}).get(b, {}).get(g) != forventet.get(u, {}).get(b, {}).get(g))
    celler = sum(len(gs) for bs in forventet.values() for gs in bs.values())
    sjekk(f"omsetning per butikk (med nettbutikken), varegruppe og ISO-uke ({celler} celler)", avvik, [])


def modul7(sql, en):
    m7 = FASIT["modul7_kunde"]
    gj = f"sys__gyldig_til = TIMESTAMP'{APEN}'"
    sjekk("slv__kunde gjeldende rader (medlemmer i siste uttrekk)", en(f"SELECT count(*) FROM slv__kunde WHERE {gj}"), m7["medlemmer_i_siste_uttrekk"])
    sjekk("gld__d__kunde rader uten -1 og -2 (alle versjoner, SCD2)",
          en("SELECT count(*) FROM gld__d__kunde WHERE pk__gld__d__kunde NOT IN (-1, -2)"), m7["gld__d__kunde_rader_uten_minus"])
    sjekk("gld__d__kunde har spesialradene -1 Ukjent og -2 Mangler",
          sql("SELECT pk__gld__d__kunde, bk__gld__d__kunde FROM gld__d__kunde WHERE pk__gld__d__kunde IN (-1, -2) ORDER BY 1"), [(-2, -2), (-1, -1)])
    sjekk("300042 har tre versjoner med nivå, postnummer og gyldighet",
          [(n, p, str(f), str(t)) for n, p, f, t in sql("""SELECT medlemsniva, postnummer, gyldig_fra, gyldig_til FROM gld__d__kunde
                                                           WHERE medlemsnummer = '300042' ORDER BY gyldig_fra""")],
          [(v["tier"], v["postalCode"], v["fra_uttrekk"].replace("T", " "), (v["til_uttrekk"] or APEN).replace("T", " "))
           for v in m7["medlem_300042_versjoner"]])
    fk = m7["fk__gld__d__kunde"]
    sjekk("fk__gld__d__kunde = -2 uten medlemskort og -1 ukjent medlem",
          dict(sql("SELECT cast(fk__gld__d__kunde AS string), count(*) FROM gld__f__salg WHERE fk__gld__d__kunde IN (-1, -2) GROUP BY 1")),
          {"-2": fk["-2_linjer"], "-1": fk["-1_linjer"]})
    sjekk("det ukjente medlemmet: medlemsnummer og salgsdato",
          [sorted(x) for x in sql("""SELECT collect_set(s.medlemsnummer), collect_set(cast(s.salg_dato AS string)) FROM slv__salgslinje s
                                     LEFT JOIN slv__kunde k ON k.bk__slv__kunde = s.fb__slv__kunde
                                     WHERE s.medlemsnummer IS NOT NULL AND k.bk__slv__kunde IS NULL""")[0]],
          [[fk["-1_medlemsnummer"]], [fk["-1_salgsdato"]]])
    kunde = "gld__f__salg f JOIN gld__d__kunde k ON k.pk__gld__d__kunde = f.fk__gld__d__kunde"
    niva = "CASE WHEN k.pk__gld__d__kunde IN (-1, -2) THEN cast(k.pk__gld__d__kunde AS string) ELSE k.medlemsniva END"
    sjekk("salg per nivå medlemmet hadde på salgsdatoen (datoeffektivt oppslag)",
          {g: {"linjer": n, "belop": r2(b)} for g, n, b in sql(f"SELECT {niva}, count(*), sum(f.belop) FROM {kunde} GROUP BY 1")},
          {g: {"linjer": v["linjer"], "belop": r2(v["belop"])} for g, v in m7["salg_per_niva_paa_salgsdato"].items()})
    naa = m7["salg_fra_dagens_gull_medlemmer"]
    sjekk("salg fra medlemmer som er Gull i dag, uansett nivå da (SCD2 gir begge svarene)",
          [(n, r2(b)) for n, b in sql(f"""SELECT count(*), sum(f.belop) FROM {kunde}
                                         JOIN gld__d__kunde naa ON naa.bk__gld__d__kunde = k.bk__gld__d__kunde
                                          AND naa.gyldig_til = TIMESTAMP'{APEN}' AND naa.pk__gld__d__kunde NOT IN (-1, -2)
                                         WHERE naa.medlemsniva = 'GOLD'""")],
          [(naa["linjer"], r2(naa["belop"]))])
    sjekk("300042: hvert kjøp med nivået på salgsdatoen",
          [(d, kanal, s, ln, n, r2(b)) for d, kanal, s, ln, n, b in sql(f"""
              SELECT cast(f.salg_dato AS string), CASE WHEN f.butikknummer = 107 THEN 'Nett' ELSE 'Butikk' END, f.salgsnummer,
                     f.linjenummer, k.medlemsniva, f.belop
              FROM {kunde} WHERE k.medlemsnummer = '300042' ORDER BY 1, 3, 4""")],
          [(v["salgsdato"], v["kanal"], v["salgsnummer"], v["linje"], v["niva_paa_salgsdato"], r2(v["belop"])) for v in m7["medlem_300042_salg"]])
    uten = m7["kvitteringer_uten_medlemskort"]
    sjekk("kvitteringer i butikk uten medlemskort",
          list(sql(f"""SELECT count(DISTINCT CASE WHEN fk__gld__d__kunde = -2 THEN concat(butikknummer, '|', salgsnummer) END),
                              count(DISTINCT concat(butikknummer, '|', salgsnummer))
                       FROM gld__f__salg WHERE {KASSE}""")[0]),
          [uten["antall"], uten["av"]])


def modul11(sql, en):
    m11 = FASIT["modul11_lager"]
    f = "gld__f__lagerbeholdning"
    sjekk(f"{f} rader (vare, butikk og dag)", en(f"SELECT count(*) FROM {f}"), m11["gld__f__lagerbeholdning_rader"])
    sjekk(f"{f} pk__ er unik", en(f"SELECT count(DISTINCT pk__{f}) FROM {f}"), m11["gld__f__lagerbeholdning_rader"])
    sjekk("tellingsdager (ingen på søndag)", en(f"SELECT count(DISTINCT telling_dato) FROM {f}"), m11["tellingsdager"])
    sjekk("dager i øyeblikksbildet (alle dager, også søndager)", en(f"SELECT count(DISTINCT dato) FROM {f}"), len(m11["sum_per_dag_og_butikk"]))
    sjekk("søndag har lørdagens telling",
          en(f"SELECT count(*) FROM {f} WHERE dayofweek(dato) = 1 AND telling_dato <> date_sub(dato, 1)"), 0)
    sjekk("fk__ treffer alltid", en(f"""SELECT count(*) FROM {f} WHERE fk__gld__d__produkt IN (-1, -2) OR fk__gld__d__butikk IN (-1, -2)
                                         OR fk__gld__d__dato IN (-1, -2)"""), 0)
    faktisk = {}
    for d, b, p, o in sql(f"SELECT cast(dato AS string), cast(butikknummer AS string), sum(antall_pa_lager), sum(antall_i_bestilling) FROM {f} GROUP BY 1, 2"):
        faktisk.setdefault(d, {})[b] = {"antall_pa_lager": p, "antall_i_bestilling": o}
    forventet = m11["sum_per_dag_og_butikk"]
    sjekk(f"sum på lager og i bestilling per dag og butikk ({len(forventet)} dager)",
          sorted(d for d in set(faktisk) | set(forventet) if faktisk.get(d) != forventet.get(d)), [])
    faktisk = {}
    for d, b, p in sql(f"SELECT cast(dato AS string), cast(butikknummer AS string), antall_pa_lager FROM {f} WHERE varenummer = '4711'"):
        faktisk.setdefault(d, {})[b] = p
    sjekk("vare 4711 på lager per dag og butikk", sorted(d for d in set(faktisk) | set(m11["vare_4711_antall_pa_lager"])
                                                         if faktisk.get(d) != m11["vare_4711_antall_pa_lager"].get(d)), [])
    sjekk("varer som gikk tomme: dag, butikk, vare, uke",
          [list(r) for r in sql(f"""SELECT cast(l.dato AS string), l.butikknummer, l.varenummer, concat(d.ar, '-W', lpad(cast(d.uke AS string), 2, '0'))
                                   FROM {f} l JOIN gld__d__dato d ON d.pk__gld__d__dato = l.fk__gld__d__dato
                                   WHERE l.antall_pa_lager = 0 ORDER BY 1, 2, 3""")],
          [[v["dato"], v["butikk"], v["varenummer"], v["uke"]] for v in m11["varer_tomme"]])
    h17 = m11["h17"]
    serie = sql(f"""SELECT cast(dato AS string), antall_pa_lager, antall_i_bestilling FROM {f}
                   WHERE butikknummer = {h17['butikk']} AND varenummer = '{h17['varenummer']}'
                     AND dato BETWEEN DATE'{min(h17['serie'])}' AND DATE'{max(h17['serie'])}' ORDER BY 1""")
    sjekk(f"vare {h17['varenummer']} i butikk {h17['butikk']} rundt uke 40",
          {d: {"antall_pa_lager": p, "antall_i_bestilling": o} for d, p, o in serie}, h17["serie"])


if __name__ == "__main__":
    main()
