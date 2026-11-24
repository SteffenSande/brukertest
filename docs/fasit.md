# Fasit for kursdataene

Generert av `tools/lag_data.py`. Ikke rediger for hånd. Alle tall står i `fasit/fasit.json`.

Tallene er regnet av programmet som lager dataene, ikke lest fra filene og ikke fra pipelinen. Salgsdato er norsk dato (Europe/Oslo) av `soldAt`/`ordered_at`. `belop = antall * enhetspris - rabatt`, kroner med mva. Nettprisen er etter rabatt, så rabatten er 0 for nettbutikken.

Periode 2026-08-01 til 2026-10-31. 457 filer i landing.

## Modul 2: raw

| Tabell | Filer | Rader |
|---|---|---|
| `raw__kalender__dag` | 1 | 730 |
| `raw__kassio__kvittering` | 92 | 19845 |
| `raw__kassio__kvitteringslinje` | 92 | 38613 |
| `raw__lagra__beholdning` | 79 | 66600 |
| `raw__lojal__medlem` | 92 | 73039 |
| `raw__nettora__ordrelinje` | 92 | 5633 |
| `raw__varius__aktor` | 3 | 50 |
| `raw__varius__vare` | 3 | 450 |
| `raw__varius__varegruppe` | 3 | 36 |

## Modul 3: bronze

| Tabell | Rader (alle versjoner) |
|---|---|
| `brz__varius__vare` | 153 |
| `brz__varius__varegruppe` | 12 |
| `brz__varius__aktor` | 17 |
| `brz__kassio__kvittering` | 19845 |
| `brz__kassio__kvitteringslinje` | 38612 |
| `brz__nettora__ordrelinje` | 5633 |
| `brz__lojal__medlem` | 808 |
| `brz__lagra__beholdning` | 66600 |
| `brz__kalender__dag` | 730 |

- `004711` har 2 versjoner: UTPRIS 1 299,00 og 1 399,00.
- Kvitteringslinjen har 1 rad mer i raw enn i bronze.

## Modul 4: sølv

- `slv__salgslinje` (kassen): 38612 rader.
- `fb__slv__produkt` uten treff: 6 linjer med varenummer 9999.
- Lillehammer: første salgsdato 2026-09-05, første `soldAt` 2026-09-04T22:05:07Z.
- Salgsdato 2026-09-12: 521 linjer, i filen som kom 14. september.
- 44 kvitteringer har UTC-dato dagen før salgsdatoen.

## Modul 5: første stjerne

- `gld__f__salg` (kassen): 38612 rader, `fk__gld__d__produkt = -1` på 6.
- Omsetning i kassen: 33 903 607,40 kr.
- Returer: 746 linjer (1,9 %), -597 483,10 kr.

| Butikk | Omsetning kasse |
|---|---|
| 101 | 8 514 732,40 |
| 102 | 6 789 954,10 |
| 103 | 5 861 131,75 |
| 104 | 5 773 993,60 |
| 105 | 4 196 621,70 |
| 106 | 2 767 173,85 |

Omsetning per butikk, varegruppe og ISO-uke: `modul5_gull_salg.omsetning_uke_butikk_varegruppe_kasse` (varegruppe etter SCD1, altså siste uttrekk).

## Modul 6: nettbutikken

- `slv__salgslinje` med nett: 44245 rader.
- Nettandel av omsetningen: 11,2 % totalt; 2026-08: 11,7 %, 2026-09: 11,1 %, 2026-10: 10,7 %.

## Modul 7: kunden

- `300042` har 3 versjoner: SILVER/0367 fra 2026-08-01, GOLD/0367 fra 2026-09-20, GOLD/7014 fra 2026-10-10.
- `fk__gld__d__kunde = -2` på 15141 linjer (uten kort), `-1` på 2 (medlem 300999).
- Kvitteringer uten medlemskort: 39,3 %.
- Nivå på salgsdato = nivået i uttrekket kl. 04 samme dag.

| Nivå på salgsdato | Linjer | Beløp |
|---|---|---|
| -1 | 2 | 558,00 |
| -2 | 15141 | 14 027 692,40 |
| BRONZE | 11116 | 9 678 714,10 |
| GOLD | 7067 | 5 312 761,85 |
| SILVER | 10919 | 9 159 204,00 |

## Modul 11: lager

- `gld__f__lagerbeholdning`: 77550 rader (søndag = lørdagens telling).
- Tomme varer: 4492 i 102 2026-09-29, 4492 i 102 2026-09-30, 4492 i 102 2026-10-01, 4492 i 102 2026-10-02, 4492 i 102 2026-10-03, 4492 i 102 2026-10-04.
