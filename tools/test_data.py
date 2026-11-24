# /// script
# requires-python = ">=3.11"
# dependencies = ["pyarrow==26.0.1"]
# ///
"""Selvtest av datageneratoren (tools/lag_data.py).

Kjør fra repo-roten:
    uv run tools/test_data.py

Kjører generatoren to ganger i tomme mapper og sjekker, ved å lese filene (ikke generatorens sannhet):
  1. determinisme: to kjøringer gir byte-like filer, og fasiten i repoet er lik den nye;
  2. filnavn og leveransetider etter design.md kap. 3.1;
  3. kolonnenavn i hver fil mot tabellene i design.md kap. 3.2 (lest fra designdokumentet);
  4. at hver hendelse H1-H17 (kap. 6) står i filene;
  5. at nøklene kobler på tvers av kildene;
  6. volum nær kap. 3.3;
  7. at fasitens filer og raw-radtall stemmer med filene.
Avslutter med kode 1 hvis noe feiler.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OSLO = ZoneInfo("Europe/Oslo")
FRA, TIL = date(2026, 8, 1), date(2026, 10, 31)
DAGER = [FRA + timedelta(days=i) for i in range((TIL - FRA).days + 1)]
TABELLER = {  # (kilde, tabell) -> (filtype, skilletegn)
    ("varius", "vare"): ("csv", ";"), ("varius", "varegruppe"): ("csv", ";"), ("varius", "aktor"): ("csv", ";"),
    ("kassio", "kvittering"): ("csv", ","), ("kassio", "kvitteringslinje"): ("csv", ","),
    ("nettora", "ordrelinje"): ("json", None), ("lojal", "medlem"): ("json", None),
    ("lagra", "beholdning"): ("parquet", None), ("kalender", "dag"): ("csv", ","),
}

ok: list[str] = []
feil: list[str] = []


def sjekk(betingelse, tekst):
    (ok if betingelse else feil).append(tekst)


def hashes(rot):
    ut = {}
    for mappe in ("data", "fasit"):
        for d, _, filer in os.walk(os.path.join(rot, mappe)):
            for f in filer:
                p = os.path.join(d, f)
                ut[os.path.relpath(p, rot)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    p = os.path.join(rot, "docs", "fasit.md")
    ut["docs/fasit.md"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return ut


def design_kolonner():
    """Kolonnene per (kilde, tabell) fra design.md kap. 3.2."""
    tekst = open(os.path.join(ROT, "docs", "design.md"), encoding="utf-8").read()
    del_ = tekst.split("### 3.2 Tabeller og kolonner")[1].split("### 3.3")[0]
    ut = defaultdict(list)
    kilde = tabell = None
    for linje in del_.splitlines():
        m = re.match(r"^\*\*(\w+)\*\*$", linje.strip())
        if m:
            kilde = m.group(1)
            continue
        if not linje.startswith("|") or linje.startswith("|---") or linje.startswith("| Tabell"):
            continue
        celler = [c.strip() for c in linje.strip().strip("|").split("|")]
        if celler[0]:
            tabell = celler[0].strip("`")
        if kilde == "kalender":
            ut[(kilde, tabell)] = re.findall(r"`([A-Z_]+)`", re.sub(r"\([^)]*\)", "", celler[1]))
        else:
            ut[(kilde, tabell)].append(celler[1].strip("`"))
    return dict(ut)


def les(rot, kilde, tabell):
    """-> {ankomst (datetime): (kolonner, rader som dict)}"""
    ext, sep = TABELLER[(kilde, tabell)]
    mappe = os.path.join(rot, "data", "landing", kilde, tabell)
    ut = {}
    for f in sorted(os.listdir(mappe)):
        m = re.match(rf"^{tabell}_(\d{{8}}T\d{{4}})\.{ext}$", f)
        assert m, f"filnavn {kilde}/{tabell}/{f}"
        ankomst = datetime.strptime(m.group(1), "%Y%m%dT%H%M")
        p = os.path.join(mappe, f)
        if ext == "csv":
            with open(p, encoding="utf-8", newline="") as fh:
                r = list(csv.reader(fh, delimiter=sep))
            ut[ankomst] = (r[0], [dict(zip(r[0], x)) for x in r[1:]])
        elif ext == "json":
            rader, kol = [], []
            with open(p, encoding="utf-8") as fh:
                for linje in fh:
                    post = json.loads(linje)
                    rader.append(post)
                    kol += [k for k in post if k not in kol]
            ut[ankomst] = (kol, rader)
        else:
            import pyarrow.parquet as pq
            t = pq.read_table(p)
            ut[ankomst] = (t.schema.names, t.to_pylist())
    return ut


def norsk(utc_tekst):
    return datetime.strptime(utc_tekst, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(OSLO).date()


def kjor_generator(rot):
    subprocess.run([sys.executable, os.path.join(ROT, "tools", "lag_data.py"), "--rot", rot], check=True, capture_output=True)


def main():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        kjor_generator(a)
        kjor_generator(b)
        ha, hb = hashes(a), hashes(b)
        sjekk(ha == hb, f"determinisme: to kjøringer gir byte-like filer ({len(ha)} filer)")
        for f in ("fasit/fasit.json", "docs/fasit.md"):
            p = os.path.join(ROT, f)
            sjekk(os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == ha[f],
                  f"{f} i repoet er lik en ny kjøring (kjør uv run tools/lag_data.py)")
        sjekk_filene(a)
        samlet = hashlib.sha256("".join(f"{k}{v}" for k, v in sorted(ha.items())).encode()).hexdigest()

    for t in ok:
        print("OK   ", t)
    for t in feil:
        print("FEIL ", t)
    print(f"\n{len(ok)} ok, {len(feil)} feil. Samlet sjekksum: {samlet}")
    sys.exit(1 if feil else 0)


def sjekk_filene(rot):
    F = {k: les(rot, *k) for k in TABELLER}
    alle_filer = sum(len(v) for v in F.values())
    vare, gruppe, aktor = F[("varius", "vare")], F[("varius", "varegruppe")], F[("varius", "aktor")]
    kv, kl = F[("kassio", "kvittering")], F[("kassio", "kvitteringslinje")]
    nett, klubb, lager, kal = F[("nettora", "ordrelinje")], F[("lojal", "medlem")], F[("lagra", "beholdning")], F[("kalender", "dag")]

    # ---- 2. filnavn og leveransetider ----
    vu = [datetime(2026, m, 1, 5, 0) for m in (8, 9, 10)]
    sjekk(all(sorted(x) == vu for x in (vare, gruppe, aktor)), "varius: fullt uttrekk 1. aug/sep/okt kl. 05")
    kasse_tider = [datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=6) for d in DAGER if d != date(2026, 9, 12)]
    kasse_tider = sorted(kasse_tider + [datetime(2026, 9, 14, 9, 30)])
    sjekk(sorted(kv) == kasse_tider and sorted(kl) == kasse_tider, "kasse: daglig fil kl. 06 for gårsdagen (92 filer per tabell)")
    sjekk(sorted(nett) == [datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=6) for d in DAGER],
          "nettora: daglig fil kl. 06 for gårsdagen (92 filer)")
    sjekk(sorted(klubb) == [datetime.combine(d, datetime.min.time()).replace(hour=4) for d in DAGER], "lojal: daglig uttrekk kl. 04 (92 filer)")
    sjekk(sorted(lager) == [datetime.combine(d, datetime.min.time()).replace(hour=23) for d in DAGER if d.weekday() != 6],
          "lagra: telling mandag til lørdag kl. 23 (79 filer)")
    sjekk(len(kal) == 1, "kalender: én fil")
    sjekk(alle_filer == 457, f"457 filer i landing (fant {alle_filer})")

    # ---- 3. kolonner mot design.md ----
    design = design_kolonner()
    for (kilde, tabell), filer in F.items():
        forventet = design[(kilde, tabell)]
        if (kilde, tabell) == ("kassio", "kvitteringslinje"):
            for ankomst, (kol, _) in filer.items():
                ventet = forventet if ankomst >= datetime(2026, 10, 2) else [c for c in forventet if c != "campaignCode"]
                if kol != ventet:
                    sjekk(False, f"kolonner {tabell} {ankomst}: {kol}")
            sjekk(True, f"kolonner {kilde}/{tabell} = design.md (campaignCode fra filene for 1. oktober)")
            continue
        avvik = [a for a, (kol, rader) in filer.items() if (rader or TABELLER[(kilde, tabell)][0] != "json") and kol != forventet]
        sjekk(not avvik, f"kolonner {kilde}/{tabell} = design.md {forventet}")

    # ---- 4. hendelsene ----
    vrader = {u: {r["VARENR"]: r for r in rader} for u, (_, rader) in vare.items()}
    aug, sep, okt = (vrader[u] for u in vu)
    # H1
    sjekk(all(re.fullmatch(r"0\d{5}", n) for n in aug), "H1: VARENR har seks tegn med ledende null")
    sjekk(all(re.fullmatch(r"0\d{5}", r["product_code"]) for _, (_, rr) in nett.items() for r in rr), "H1: product_code med ledende nuller")
    sjekk(all(not r["sku"].startswith("0") for _, (_, rr) in kl.items() for r in rr), "H1: sku uten ledende nuller")
    sjekk(all(isinstance(r["item_no"], int) for _, (_, rr) in lager.items() for r in rr), "H1: item_no er heltall")
    # H2
    sjekk(all(re.fullmatch(r"\d+,\d\d", r["UTPRIS"]) for r in aug.values()), "H2: UTPRIS med desimalkomma")
    sjekk(all(re.fullmatch(r"\d\d\.\d\d\.\d{4}", r["AAPNET_DT"]) for _, (_, rr) in aktor.items() for r in rr if r["AKTTYPE"] == "B"),
          "H2: AAPNET_DT som dd.MM.yyyy")
    # H3, H4, H6 og stabilitet: alle forskjeller mellom uttrekkene
    endr = set()
    for a_, b_ in ((aug, sep), (sep, okt)):
        sjekk(set(a_) == set(b_), "varius: samme varer i alle uttrekk")
        for n in a_:
            for k in a_[n]:
                if a_[n][k] != b_[n][k]:
                    endr.add((n, k, a_[n][k], b_[n][k], "sep" if b_ is sep else "okt"))
    h3 = {e for e in endr if e[0] == "004711"}
    sjekk(h3 == {("004711", "UTPRIS", "1299,00", "1399,00", "okt")}, f"H3: 004711 får ny utpris i uttrekket 1. oktober {h3}")
    h4 = {e for e in endr if e[1] == "VGRP"}
    sjekk(len(h4) == 1 and next(iter(h4))[4] == "sep", f"H4: én vare bytter varegruppe i uttrekket 1. september {h4}")
    h6 = {e for e in endr if e[1] == "STATUS"}
    sjekk(len(h6) == 1 and next(iter(h6))[2:] == ("A", "U", "okt") and all(r["STATUS"] == "A" for r in aug.values()),
          f"H6: én vare blir utgått i uttrekket 1. oktober {h6}")
    sjekk(len(endr) == 3, f"stabilt: ingen andre endringer i varesystemet enn H3/H4/H6 ({len(endr)} endringer)")
    g = [tuple(tuple(r.items()) for r in rr) for _, (_, rr) in sorted(gruppe.items())]
    sjekk(len(set(g)) == 1, "stabilt: varegruppe lik i alle uttrekk")
    akt = {u: {r["AKTNR"]: r for r in rr} for u, (_, rr) in aktor.items()}
    sjekk("106" not in akt[vu[0]] and akt[vu[1]]["106"]["AAPNET_DT"] == "05.09.2026" and "106" in akt[vu[2]],
          "H5: Lillehammer (106) i aktor fra uttrekket 1. september, åpnet 05.09.2026")
    sjekk(all(akt[vu[0]][k] == akt[u][k] for u in vu[1:] for k in akt[vu[0]]), "stabilt: aktørene uendret mellom uttrekk")
    sjekk(akt[vu[2]]["107"]["KOMMUNE"] == "" and any(r["KOMMUNE"] == "" for r in akt[vu[2]].values() if r["AKTTYPE"] == "L")
          and all(r["ORGNR"] == "" for r in akt[vu[2]].values() if r["AKTTYPE"] == "B"),
          "aktor: KOMMUNE tom for nettbutikken og noen leverandører, ORGNR bare for leverandører")
    sjekk(sorted(int(k) for k in akt[vu[2]]) == list(range(101, 108)) + list(range(501, 511)), "aktor: butikker 101-107, leverandører 501-510")

    kvitt = [r | {"_fil": a} for a, (_, rr) in kv.items() for r in rr]
    linjer = [r | {"_fil": a} for a, (_, rr) in kl.items() for r in rr]
    lh = [r for r in kvitt if r["storeId"] == "106"]
    sjekk(min(norsk(r["soldAt"]) for r in lh) == date(2026, 9, 5), "H5: Lillehammer har salg fra 5. september (norsk dato)")
    sjekk(min(r["soldAt"] for r in lh).startswith("2026-09-04"), "H5/H13: Lillehammers første soldAt er 4. september i UTC")
    # H7
    uten = sum(1 for r in kvitt if r["memberNo"] == "") / len(kvitt)
    sjekk(0.35 <= uten <= 0.45, f"H7: kvitteringer uten memberNo {uten:.1%}")
    # H8
    h8 = [r for r in linjer if r["sku"] == "9999"]
    sjekk(h8 and all(r["receiptNo"].startswith("20260814") for r in h8) and "009999" not in aug,
          f"H8: {len(h8)} linjer med sku 9999, bare 14. august, ikke i varesystemet")
    # H9
    retur = sum(1 for r in linjer if int(r["qty"]) < 0) / len(linjer)
    sjekk(0.015 <= retur <= 0.025, f"H9: returlinjer {retur:.2%}")
    # H10
    kamp = [r for r in linjer if r.get("campaignCode")]
    sjekk(kamp and all(r["receiptNo"] >= "20261001" for r in kamp) and {r["campaignCode"] for r in kamp} == {"HOST26"},
          f"H10: campaignCode HOST26 på {len(kamp)} linjer fra 1. oktober")
    # H11
    dupl = []
    for a, (_, rr) in kl.items():
        c = Counter(tuple(r.values()) for r in rr)
        dupl += [(a, k) for k, n in c.items() if n > 1]
    sjekk(len(dupl) == 1 and dupl[0][0] == datetime(2026, 8, 22, 6, 0) and dupl[0][1][1].startswith("20260821"),
          f"H11: én linje står to ganger, i filen for 21. august ({[(str(a), k[1], k[2]) for a, k in dupl]})")
    # H12
    sen = datetime(2026, 9, 14, 9, 30)
    sjekk(datetime(2026, 9, 13, 6, 0) not in kv and {r["receiptNo"][:8] for r in kv[sen][1]} == {"20260912"},
          "H12: filene for 12. september kom 14. september (ingen fil 13. september kl. 06)")
    # H13
    h13k = [r for r in kvitt if r["soldAt"][:10] != norsk(r["soldAt"]).isoformat()]
    sjekk(len({r["receiptNo"][:8] for r in h13k}) >= 2, f"H13: {len(h13k)} kvitteringer med UTC-dato før norsk dato, flere dager")
    sjekk(all(r["receiptNo"][:8] == norsk(r["soldAt"]).strftime("%Y%m%d") for r in kvitt),
          "kasse: datoen i receiptNo er den norske datoen")
    sjekk(any(r["soldAt"].startswith("2026-10-30T23") for r in h13k), "H13: kjøp etter overgangen til vintertid (UTC+1)")
    nlinjer = [r | {"_fil": a} for a, (_, rr) in nett.items() for r in rr]
    h13n = [r for r in nlinjer if r["ordered_at"][:10] != norsk(r["ordered_at"]).isoformat()]
    sjekk(len(h13n) > 0, f"H13: {len(h13n)} nettlinjer med UTC-dato før norsk dato")
    sjekk(all(r["_fil"].date() - timedelta(days=1) == norsk(r["ordered_at"]) for r in nlinjer), "nett: hver fil har gårsdagens norske dato")
    sjekk(all(r["_fil"] == sen or r["_fil"].date() - timedelta(days=1) == norsk(r["soldAt"]) for r in kvitt),
          "kasse: hver fil har gårsdagens norske dato (unntatt H12)")
    # H14
    m42 = {a.date(): next(r for r in rr if r["memberId"] == 300042) for a, (_, rr) in klubb.items()}
    niva = {d: (m["tier"], m["postalCode"]) for d, m in m42.items()}
    sjekk(all(niva[d] == ("SILVER", "0367") for d in DAGER if d < date(2026, 9, 20))
          and all(niva[d] == ("GOLD", "0367") for d in DAGER if date(2026, 9, 20) <= d < date(2026, 10, 10))
          and all(niva[d] == ("GOLD", "7014") for d in DAGER if d >= date(2026, 10, 10)),
          "H14: 300042 Sølv til Gull 20. september, flytter 10. oktober")
    forrige, endringer, nye = None, [], 0
    for a in sorted(klubb):
        naa = {r["memberId"]: r for r in klubb[a][1]}
        if forrige:
            sjekk_borte = set(forrige) - set(naa)
            if sjekk_borte:
                endringer.append(("borte", a, sjekk_borte))
            nye += len(set(naa) - set(forrige))
            endringer += [(m, a) for m in forrige if m in naa and forrige[m] != naa[m]]
        forrige = naa
    sjekk(sorted(e[0] for e in endringer) == [300042, 300042], f"stabilt: bare 300042 endres i kundeklubben ({len(endringer)} endringer)")
    # H15
    medlemmer_dag = {a.date(): {r["memberId"] for r in rr} for a, (_, rr) in klubb.items()}
    ukjent = [r for r in nlinjer if r["customer_id"] not in medlemmer_dag[norsk(r["ordered_at"])]]
    sjekk(ukjent and {r["customer_id"] for r in ukjent} == {300999} and {norsk(r["ordered_at"]) for r in ukjent} == {date(2026, 10, 3)}
          and all(300999 not in s for s in medlemmer_dag.values()),
          f"H15: nettordre fra 300999 (ikke i kundeklubben) 3. oktober, ingen andre ukjente ({len(ukjent)} linjer)")
    # H16
    sjekk(not any(a.weekday() == 6 for a in lager), "H16: ingen lagertelling på søndager")
    sjekk(all(r["count_date"] == a.date() for a, (_, rr) in lager.items() for r in rr), "lager: count_date = tellingsdagen i filnavnet")
    # H17
    tomme = [(r["count_date"], r["whs_store"], r["item_no"]) for _, (_, rr) in lager.items() for r in rr if r["on_hand"] == 0]
    sjekk(tomme and all(d.isocalendar()[1] == 40 for d, _, _ in tomme) and len({(b, i) for _, b, i in tomme}) == 1,
          f"H17: én vare tom i én butikk, bare i uke 40 ({len(tomme)} tellinger)")
    if tomme:
        _, tb, ti = tomme[0]
        solgt_tom = [r for r in linjer if r["storeId"] == str(tb) and r["sku"] == str(ti)
                     and date(2026, 9, 29) < datetime.strptime(r["receiptNo"][:8], "%Y%m%d").date() < date(2026, 10, 5)]
        sjekk(not solgt_tom, "H17: ingen salg av varen i butikken mens den er tom")
    sjekk(all(r["on_hand"] >= 0 and r["on_order"] >= 0 for _, (_, rr) in lager.items() for r in rr), "lager: ingen negative tall")

    # ---- 5. nøklene kobler ----
    varenr = {n.lstrip("0") for n in aug}
    sjekk({r["sku"] for r in linjer} - varenr == {"9999"}, "kobling: alle sku finnes i varesystemet, unntatt 9999")
    sjekk({r["product_code"] for r in nlinjer} <= set(aug), "kobling: alle product_code finnes i varesystemet")
    sjekk({str(r["item_no"]) for _, (_, rr) in lager.items() for r in rr} == varenr, "kobling: lageret har alle varene")
    butikker = {k for k, r in akt[vu[2]].items() if r["AKTTYPE"] == "B"}
    sjekk({r["storeId"] for r in kvitt} == butikker - {"107"}, "kobling: storeId er butikkene 101-106")
    sjekk({str(r["whs_store"]) for _, (_, rr) in lager.items() for r in rr} == butikker - {"107"}, "kobling: whs_store er butikkene 101-106")
    sjekk(all(r["LEVNR"] in akt[vu[0]] and akt[vu[0]][r["LEVNR"]]["AKTTYPE"] == "L" for r in aug.values()), "kobling: LEVNR er leverandører")
    sjekk(all(r["VGRP"] in {x["VGRP"] for x in gruppe[vu[0]][1]} for r in aug.values()), "kobling: VGRP finnes i varegruppe")
    hoder = {(r["storeId"], r["receiptNo"]) for r in kvitt}
    sjekk(all((r["storeId"], r["receiptNo"]) in hoder for r in linjer)
          and len(hoder) == len(kvitt) and {(r["storeId"], r["receiptNo"]) for r in linjer} == hoder,
          "kobling: hver linje har et hode, hvert hode har linjer, receiptNo unikt per butikk")
    sjekk(all(r["memberNo"] == "" or int(r["memberNo"]) in medlemmer_dag[norsk(r["soldAt"])] for r in kvitt),
          "kobling: memberNo i kassen finnes i kundeklubbens uttrekk samme dag")
    sjekk(all(re.fullmatch(r"300\d{3}", str(m)) for s in medlemmer_dag.values() for m in s), "lojal: medlemsnumre 300xxx")
    sjekk(all(re.fullmatch(r"\d{4}", r["postalCode"]) for r in klubb[max(klubb)][1]), "lojal: postnummer med fire tegn (tekst)")
    ordre = defaultdict(set)
    for r in nlinjer:
        ordre[r["order_id"]].add((r["customer_id"], r["ordered_at"]))
    sjekk(all(len(v) == 1 for v in ordre.values()), "nett: én kunde og ett tidspunkt per ordre")
    sjekk(all(r["customer_id"] is not None for r in nlinjer), "nett: customer_id alltid fylt")

    # ---- 6. volum (kap. 3.3) ----
    apne = [d for d in DAGER if d.weekday() != 6]
    per_kv = Counter((r["storeId"], r["receiptNo"]) for r in linjer)
    sjekk(140 <= len(aug) <= 160 and len(gruppe[vu[0]][1]) == 12 and sum(1 for r in akt[vu[0]].values() if r["AKTTYPE"] == "L") == 10,
          f"volum: {len(aug)} varer, 12 varegrupper, 10 leverandører")
    sjekk(750 <= len(klubb[max(klubb)][1]) <= 850, f"volum: {len(klubb[max(klubb)][1])} medlemmer")
    snitt = len(kvitt) / len(apne)
    sjekk(225 <= snitt <= 275, f"volum: {snitt:.0f} kvitteringer per åpningsdag (stengt søndag)")
    sjekk(set(per_kv.values()) <= {1, 2, 3, 4}, "volum: 1-4 linjer per kvittering (dublettlinjen fra H11 telles ikke)")
    no = len(ordre) / len(DAGER)
    sjekk(35 <= no <= 45, f"volum: {no:.1f} nettordrer per dag")
    lr = [len(rr) for a, (_, rr) in lager.items() if a.date() >= date(2026, 9, 5)]
    sjekk(set(lr) == {900}, "volum: 900 lagerrader per tellingsdag fra Lillehammer åpnet (750 før)")

    # ---- 7. fasit mot filene ----
    fasit = json.load(open(os.path.join(rot, "fasit", "fasit.json"), encoding="utf-8"))
    raw = fasit["modul2_raw"]["rader_per_tabell"]
    for (kilde, tabell), filer in F.items():
        navn = kilde
        n = sum(len(rr) for _, rr in filer.values())
        sjekk(raw.get(f"raw__{navn}__{tabell}", {}).get("rader") == n and raw[f"raw__{navn}__{tabell}"]["filer"] == len(filer),
              f"fasit: raw__{navn}__{tabell} {len(filer)} filer, {n} rader")
    sjekk(fasit["filer"]["antall"] == alle_filer, "fasit: antall filer")
    sjekk(fasit["modul4_solv"]["fb__slv__produkt_uten_treff"]["linjer"] == len(h8), "fasit: antall 9999-linjer")
    sjekk(fasit["modul3_bronze"]["kvitteringslinje_raw_minus_bronze"] == 1, "fasit: raw har én kvitteringslinje mer enn bronze")
    sjekk(len(fasit["modul7_kunde"]["medlem_300042_versjoner"]) == 3, "fasit: 300042 har tre versjoner")
    sjekk(len(fasit["modul3_bronze"]["vare_004711_versjoner"]) == 2, "fasit: 004711 har to versjoner")
    sjekk(fasit["modul7_kunde"]["fk__gld__d__kunde"]["-1_linjer"] == len(ukjent), "fasit: fk__gld__d__kunde = -1 stemmer med filene")
    sjekk(fasit["modul7_kunde"]["kvitteringer_uten_medlemskort"]["antall"] == sum(1 for r in kvitt if r["memberNo"] == ""),
          "fasit: kvitteringer uten kort stemmer med filene")
    sjekk(len(fasit["modul11_lager"]["varer_tomme"]) == len(tomme) + 1, "fasit: tomme varer = tellingene + søndagen (H16)")
    sjekk(fasit["modul11_lager"]["gld__f__lagerbeholdning_rader"] == 150 * (5 * 92 + (TIL - date(2026, 9, 5)).days + 1),
          "fasit: lagerfaktaen har én rad per vare, butikk og dag")


if __name__ == "__main__":
    main()
