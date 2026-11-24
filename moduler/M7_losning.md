# Modul 7: Løsning

## Slik skal modellen se ut

**Fra `fyll M7`:** `raw__lojal__medlem` (raw, kildesystem `lojal`: JSON, datoformat `yyyy-MM-dd`, uttrekk `Fullt`) og
`brz__lojal__medlem` (BK `memberId`, `joinedDate` som `date`, `tier` med rensing `trim` og `store_bokstaver`).

**`slv__kunde`** (sølv, BK `medlemsnummer`): `medlemsnummer`, `etternavn`, `fornavn`, `innmeldt_dato`, `medlemsniva`,
`postnummer`, alle med oppstrøm i `brz__lojal__medlem` og navnet fra nedstrømsnavnet.

**`slv__salgslinje`**, ny kolonne: `fb__slv__kunde` (bigint, FK), oppstrøm `brz__kassio__kvittering.memberNo` og
`brz__nettora__ordrelinje.customer_id`, relasjon til `slv__kunde.bk__slv__kunde` (`0..N` / `0..1`).

**`gld__d__kunde`** (gull dimensjon, Historikk SCD2, BK `medlemsnummer`): kolonnene i tabellen i steg 4. `gyldig_fra` og
`gyldig_til` har flagget «Eget navn» og et utviklernotat. Fasit er sortert («Sorter kolonner»). Sjekken godtar også
en usortert tabell.

**`gld__f__salg`**, to nye kolonner:
- `salg_dato` (date), oppstrøm `slv__salgslinje.salg_dato`
- `fk__gld__d__kunde` (bigint, FK), oppstrøm `slv__salgslinje.fb__slv__kunde`, relasjon til
  `gld__d__kunde.pk__gld__d__kunde` (`0..N` / `1`), «Datoeffektiv på» = `salg_dato`

## Den genererte koden (svar på «Din tur» i steg 6)

| Valget | Linjen |
|---|---|
| Historikk SCD2 | `historikk="SCD2",` i `gld__d__kunde.py` |
| «Datoeffektiv på» | `fakta = sla_opp_nokkel(fakta, "fk__gld__d__kunde", dimensjon="gld__d__kunde", datoeffektiv_pa="salg_dato")` i `gld__f__salg.py` |
| `fb__slv__kunde` i grenen for kassen | `"fb__slv__kunde": nokkel_av("brz__kassio__kvittering.memberNo", ikke_funnet_nar=ingen_treff("brz__kassio__kvitteringslinje.storeId", "brz__kassio__kvittering.storeId")),` |
| `fb__slv__kunde` i grenen for nettbutikken | `"fb__slv__kunde": nokkel_av("brz__nettora__ordrelinje.customer_id"),` |

`ikke_funnet_nar` er med fordi medlemsnummeret i kassen kommer fra kvitteringshodet, en annen tabell enn hovedtabellen.
Finnes ikke hodet, blir nøkkelen «ikke funnet» (`-1`), ikke «tom» (`-2`). Oppslaget med «Datoeffektiv på» står i
`sla_opp_nokkel` i `databricks/pyspark/plattform/gull.py`: versjonen der `gyldig_fra < salg_dato + 1 dag <= gyldig_til`.

## Tallene

| Hva | Forventet |
|---|---|
| `raw__lojal__medlem` | 73 039 rader i 92 filer |
| `brz__lojal__medlem` | 808 rader (alle versjoner) |
| `slv__kunde` | 808 rader (alle versjoner), 806 av dem gjeldende |
| `gld__d__kunde` | 810 rader: 808 versjoner, `-1` og `-2` |
| `fk__gld__d__kunde = -2` | 15 141 linjer, 14 027 692,40 kr (kjøp uten kort) |
| `fk__gld__d__kunde = -1` | 2 linjer, 558,00 kr: nettordre fra `300999` 2026-10-03 |
| Gull da de handlet | 7 067 linjer, 5 312 761,85 kr |
| Gull i dag, uansett da | 7 073 linjer, 5 315 915,45 kr |
| Kvitteringer uten medlemskort | 7 792 av 19 845 (39,3 %) |

Kjøpene til `300042`:

| Salgsdato | Kanal | Salgsnummer | Linje | Nivå den dagen | Beløp |
|---|---|---|---|---|---|
| 2026-08-15 | Butikk | 20260815-101-0024 | 1 | SILVER | 1 529,10 |
| 2026-08-23 | Nett | N-2026-006146 | 1 | SILVER | 809,10 |
| 2026-09-06 | Nett | N-2026-006698 | 1 | SILVER | 539,10 |
| 2026-09-10 | Butikk | 20260910-101-0019 | 1-3 | SILVER | 71,10 + 116,10 + 89,10 |
| 2026-09-26 | Butikk | 20260926-101-0018 | 1-3 | GOLD | 254,15 + 338,30 + 679,15 |
| 2026-10-04 | Nett | N-2026-007815 | 1 | GOLD | 1 529,15 |
| 2026-10-17 | Butikk | 20261017-101-0017 | 1 | GOLD | 67,15 |
| 2026-10-24 | Nett | N-2026-008657 | 1 | GOLD | 254,15 |

## Svar på «Hva tror du?» og «Tenk over»

**Fornavn og etternavn (steg 4).** Analysen trenger nivå, sted og hvor lenge noen har vært medlem, ikke navn. Navn er
personopplysninger (kildearket sier det). Det som ikke trengs, tas ikke med videre. Navnet står i sølv for dem som har
en grunn til å slå det opp, og tilgangen til sølv kan styres strengere enn til gull (modul 8).

**De seks linjene (steg 7).** `300042` handlet seks linjer for 3 153,60 kr mens medlemmet var Sølv. I dag er det Gull.
Spør du «hva handler dagens Gull-medlemmer», er linjene med. Spør du «hva handler medlemmer når de er Gull», er de ikke.
SCD2 gir begge svarene. Med SCD1 ville du bare fått det første.

**Hvilket tall (steg 7).** «Hva er Gull-nivået verdt» handler om hva medlemmene gjør mens de er Gull: 5 312 761,85 kr,
nivået på salgsdatoen. Tallet for dagens Gull-medlemmer blander inn tiden før de ble Gull.

**Postnummeret (steg 8).** Kjøpet 4. oktober har versjonen med `0367`, kjøpet 17. oktober versjonen med `7014`. Analyse
per postnummer følger da medlemmet dit det bodde da det handlet.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra forhåndssjekken på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| SCD2 uten `gyldig_fra` og `gyldig_til` | `gld__d__kunde: Dimensjonen er SCD2, men har ikke kolonnen gyldig_fra. I Specly: legg til gyldig_fra (timestamp) med oppstrøm sys__gyldig_fra i sølv.` og det samme for `gyldig_til` | En versjon må si når den gjaldt |
| `gyldig_fra` uten «Eget navn» | `gld__d__kunde: Kolonnen gyldig_fra har oppstrøm slv__kunde.sys__gyldig_fra, som har nedstrømsnavnet «sys__gyldig_fra». … eller sett flagget «Eget navn» på gyldig_fra når navnet skal avvike med vilje.` | Lært i modul 4: et navn som avviker med vilje, merkes |
| Glemte Historikk | `gld__d__kunde: Gull-dimensjonen har ikke feltet Historikk (SCD1 eller SCD2). I Specly: velg Historikk på tabellen.` | Koden må vite SCD1 eller SCD2 |
| Glemte «Datoeffektiv på» | `gld__f__salg: Kolonnen fk__gld__d__kunde peker på SCD2-dimensjonen gld__d__kunde, men har ikke «Datoeffektiv på», så koden vet ikke hvilken versjon den skal velge. …` | Mot en SCD2-dimensjon må koden vite dagen |
| «Datoeffektiv på» = `salg_dato` uten kolonnen i faktaen | `gld__f__salg: «Datoeffektiv på» på fk__gld__d__kunde er salg_dato, som ikke er en kolonne i tabellen. I Specly: velg en datokolonne i tabellen.` | Feltet peker på en kolonne i samme tabell |

**Feil forhåndssjekken ikke ser** (prøvd med lokal Spark på en kopi av løsningen):
- **`fb__slv__kunde` bare fra kassen.** Gyldig, men nettbutikkens 5 633 linjer får ingen kunde: `fk__gld__d__kunde = -1`
  på alle. Nettkundene forsvinner fra svaret per nivå. Kontroll: `-1` skal være 2 linjer.
- **Historikk SCD1 på `gld__d__kunde`.** Gyldig (og «Datoeffektiv på» brukes ikke). Alle kjøp får nivået medlemmet har
  i dag: GOLD blir 7 073 linjer og 5 315 915,45 kr, SILVER 10 913 linjer. Det er svaret på et annet spørsmål.
- **«Datoeffektiv på» på en annen dato** (for eksempel `innmeldt_dato`, om den sto i faktaen). Gyldig, men koden slår
  opp versjonen ved slutten av innmeldingsdagen. Ingen versjon gjaldt da: et medlem står først i uttrekket dagen etter,
  og uttrekkene starter 1. august. Alle kjøp blir `-1`.

## Kjente Specly-feil i denne modulen

- «+ Opprett ny tabell»: navnet står ikke alltid åpent for skriving. Skriver du med en gang, kan tabellen bli hetende
  «Ny tabell 1». Klikk i navnet og skriv det på nytt, før du velger tabelltype.
- Har du vært innom konfliktsiden i en tidligere modul, kan Specly vise hver oppstrømskolonne to ganger på de gamle
  kolonnene i `slv__salgslinje` og `gld__f__salg`. De nye kolonnene vises riktig, og filene i Git er riktige.
