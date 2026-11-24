# Modul 3: Løsning

## Slik skal modellen se ut

Fem bronze-tabeller. Alle har standardkolonnene `pk__<tabell>` (PK), `bk__<tabell>`, `sys__gyldig_fra`,
`sys__gyldig_til` og `sys__kildesystem`. Hver kildekolonne har nøyaktig én oppstrøm: kolonnen med samme navn i
raw-tabellen.

| Tabell | Kildesystem | BK | Datatyper som ikke er `string` |
|---|---|---|---|
| `brz__varius__vare` | varius | `VARENR` | `LEVNR` int, `UTPRIS` decimal(10,2) |
| `brz__varius__varegruppe` | varius | `VGRP` | |
| `brz__varius__aktor` | varius | `AKTNR` | `AKTNR` int, `AAPNET_DT` date |
| `brz__kassio__kvittering` | kassio | `storeId`, `receiptNo` | `storeId` int, `soldAt` timestamp |
| `brz__kassio__kvitteringslinje` | kassio | `storeId`, `receiptNo`, `lineNo` | `storeId`, `lineNo`, `qty` int, `unitPrice`, `discount` decimal(10,2) |

Rensing og nedstrømsnavn står i tabellene i modulteksten. Fasit for hele modellen ligger pakket i
`.startpunkter/fasit-M3.startpunkt` (det `./kurs til fasit/M3` henter).

## Den genererte koden (svar på «Din tur» i steg 4)

Fra `databricks/pyspark/tabeller/brz__varius__vare.py`:

| Valget i Specly | Linjen |
|---|---|
| Datoformat og desimaltegn | `KILDEFORMAT = Kildeformat(dato="dd.MM.yyyy", desimaltegn=",")` |
| `decimal(10,2)` på `UTPRIS` | `Rens("UTPRIS", til_type="decimal(10,2)"),` |
| Rensingen på `VARENR` | `Rens("VARENR", rensing=["trim", "fjern_ledende_nuller"]),` |
| Oppstrømmen | `les_tabell("raw__varius__vare"),` |
| BK på `VARENR` | `nokkel=["VARENR"],` i `lag_historikk` |
| Uttrekk `Fullt` | `fullt_uttrekk=True,` |

For kassen ser du `KILDEFORMAT = Kildeformat(tid="yyyy-MM-dd'T'HH:mm:ssX", desimaltegn=".", tidssone="UTC")` og
`fullt_uttrekk=False`, fordi kassen bare sender nye rader.

## Tallene

| Tabell | Rader (alle versjoner) | Gjeldende |
|---|---|---|
| `brz__varius__vare` | 153 | 150 |
| `brz__varius__varegruppe` | 12 | 12 |
| `brz__varius__aktor` | 17 | 17 |
| `brz__kassio__kvittering` | 19 845 | |
| `brz__kassio__kvitteringslinje` | 38 612 | |

- `4711` (`004711` i kilden): `UTPRIS` 1 299,00 fra uttrekket 2026-08-01 05:00 til 2026-10-01 05:00, og 1 399,00 fra 2026-10-01 05:00.
- Varer med to versjoner: `003178`, `004711`, `006652`. I bronze står de uten ledende nuller: `3178`, `4711`, `6652`.
- Kvitteringslinjen har 1 rad mer i raw enn i bronze (filen `kvitteringslinje_20260822T0600.csv`).
- `AAPNET_DT` for Lillehammer (106) er 2026-09-05.

## Svar på «Tenk over»

**Hvorfor står nedstrømsnavnet ikke i bronze-koden?** Det er en beskjed til neste lag, ikke noe bronze gjør. Bronze
beholder kildens navn. Sølv-koden bruker nedstrømsnavnet, fordi sølvkolonnen får det som navn.

**Hvorfor `aktornummer` og ikke `butikknummer`?** `aktor` har både butikker og leverandører. `AKTNR` er nummeret på en
aktør, ikke alltid en butikk. Nedstrømsnavnet er derfor det generelle navnet, helst kildesystemets egen
fellesbetegnelse. I sølv blir det `butikknummer` i `slv__butikk` og `leverandornummer` i `slv__leverandor` (modul 4).

**Hvorfor rense `sku` når kassen skriver uten nuller?** Fordi nøklene skal treffe hverandre uansett hva kilden gjør.
Samme rensing på begge sider gjør at `004711` og `4711` alltid blir `4711`. Begynner kassen å skrive nuller en dag,
virker koblingen fortsatt.

**Hvorfor har `AKTTYPE` og `paymentType` ikke nedstrømsnavn?** De hentes ikke inn i sølv som kolonner. `AKTTYPE` brukes
bare i radfilteret i sølv (modul 4). Uten nedstrømsnavn får kolonnen samme navn hvis noen henter den senere. Det
stopper ikke noe.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra `./generer` på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Døpte `VARENR` om til `varenummer` | `brz__varius__vare: Kolonnen varenummer heter ikke det samme som raw-kolonnen VARENR. Bronze beholder kildens navn; det nye navnet er nedstrømsnavnet. I Specly: gi kolonnen navnet VARENR, og skriv varenummer som nedstrømsnavn.` | Det nye navnet hører hjemme i nedstrømsnavnet |
| Glemte BK | `brz__varius__vare: Tabellen har ingen kolonne med BK-flagg, så nøkkelen (bk__/pk__) kan ikke regnes ut. I Specly: sett BK-flagget på de naturlige nøkkelkolonnene.` | Uten BK ingen nøkkel og ingen historikk |
| Satte BK på `bk__brz__varius__vare` | `brz__varius__vare: Kolonnen bk__brz__varius__vare har BK-flagget. BK står på de naturlige nøkkelkolonnene, aldri på bk__ eller pk__. I Specly: ta BK-flagget av bk__brz__varius__vare og sett det på kolonnene som sammen gjør raden unik.` | `bk__` er resultatet, ikke kilden |
| Glemte kildesystemet på bronze-tabellen | `brz__varius__vare: Tabellen har ikke kildesystem, så koden vet ikke filformat og tekstformat. I Specly: gi tabellen et kildesystem under «Kildesystemer» (modul 2, steg 4).` | Kjør «Auto-tagg tabeller» etter at tabellen finnes |
| Glemte Desimaltegn på varius | `brz__varius__vare: Kolonnen UTPRIS skal gjøres om fra string til decimal(10,2), men kildesystemet varius har ikke desimaltegn. I Specly: fyll ut Desimaltegn på kildesystemet varius.` | Formatet står på kildesystemet |
| Glemte Datoformat på varius | `brz__varius__aktor: Kolonnen AAPNET_DT skal gjøres om fra string til date, men kildesystemet varius har ikke datoformat. I Specly: fyll ut Datoformat på kildesystemet varius.` | Samme |
| Glemte Tidsformat på kassio | `brz__kassio__kvittering: Kolonnen soldAt skal gjøres om fra string til timestamp, men kildesystemet kassio har ikke tidsformat. I Specly: fyll ut Tidsformat på kildesystemet kassio.` | Samme |
| Glemte Uttrekk på varius | `brz__varius__vare: Kildesystemet varius har ikke Uttrekk (Fullt eller Endringer), så historikken vet ikke om en rad som mangler er borte. I Specly: fyll ut Uttrekk på kildesystemet varius.` (én linje per vare-tabell) | Historikken må vite om en manglende rad er slettet |
| Glemte datatypen helt | `brz__varius__vare: Kolonnen UTPRIS har ingen datatype. I Specly: velg datatype på kolonnen.` | Hver kolonne trenger en type |

**Feil forhåndssjekken ikke ser:**
- **`UTPRIS` står som `string`.** Gyldig i bronze. Feilen viser seg først i sølv, der `utpris_belop` må være et beløp
  (decimal), og sjekken da sier at typen ikke stemmer med oppstrømmen. Sett typen i bronze.
- **Feil desimaltegn** (`.` i stedet for `,`). Casten gir tomme verdier i stedet for å stoppe. Kontrollen viser det:
  `SELECT count(*) FROM brz__varius__vare WHERE UTPRIS IS NULL` skal gi 0.
- **Glemt `fjern_ledende_nuller` på `VARENR`.** Bronze blir riktig nok, men i sølv treffer ikke varene i kassen
  produktene (`fb__slv__produkt` uten treff på nesten alle linjer, modul 4).
- **BK med for få kolonner** (bare `receiptNo` på kvitteringslinjen). Koden regner da samme nøkkel for ulike linjer, og
  bronze får langt færre rader enn 38 612.
- **Glemt nedstrømsnavn.** Ingen feil i bronze. I sølv får kolonnen kildens navn (`VARETEKST`), og forhåndssjekken
  stopper der fordi navnet har store bokstaver.

## Kjente Specly-feil i denne modulen

- Nye kolonner legges etter `sys__`-kolonnene. «Bruk regler» → «Sorter kolonner» rydder.
- «Sorter kolonner» står nederst i menyen «Bruk regler». Specly spør først («Sortere kolonnene?», «Avbryt» eller
  «Sorter»), og sorteringen kan ikke angres med Ctrl+Z. Den stiller også BK-kolonnene alfabetisk. I kvitteringslinjen
  blir de `lineNo`, `receiptNo`, `storeId`, og koden får `nokkel=["lineNo", "receiptNo", "storeId"]`. Fasit har samme
  rekkefølge, så i bronze er det riktig å sortere.
- Klikker du i en celle (flagg, rensing, datatype) rett etter at du lukket listen i den forrige, åpner ikke listen
  seg. Vent et sekund og klikk igjen.
- Søkefeltet i rensing-listen tømmes ikke etter et valg. Slett teksten før du søker på neste rensing.
- «+ datatype» i dialogen «Opprett kolonne med oppstrøm» ser ut som en knapp, men er det ikke.
- Endrer du datatypen på en raw-kolonne senere, endres den ikke i bronze. Det kan være meningen.
- Specly mangler et eget valg «Lag bronze fra raw». Til da henter du kolonnene samlet i dialogen.
