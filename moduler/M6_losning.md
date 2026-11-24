# Modul 6: Løsning

## Slik skal modellen se ut

**`raw__nettora__ordrelinje`** (raw, kildesystem `nettora`, «Unntatt fra sortering»): `order_id`, `line_no`,
`customer_id`, `ordered_at`, `product_code`, `quantity`, `price` (alle `string`), og de fire `sys__`-kolonnene.
Kildesystemet `nettora` har filformat `json`, desimaltegn `.`, tidsformat `yyyy-MM-dd'T'HH:mm:ssX`, tidssone `UTC` og
uttrekk `Endringer` (fra kildearket).

**Fra `fyll M6`:** `brz__nettora__ordrelinje` (bronze), med BK på `line_no` og `order_id`, og nedstrømsnavnene i tabellen
i steg 2. `product_code` har rensing `trim` og `fjern_ledende_nuller`, så `004711` blir `4711` som i kassen.

**`slv__salgslinje`** (sølv, «Union av» = `brz__kassio__kvitteringslinje`, `brz__nettora__ordrelinje`):

| Kolonne | Oppstrøm i kassen | Oppstrøm i nettbutikken | Beregning |
|---|---|---|---|
| `fb__slv__butikk` | `kvitteringslinje.storeId` | | `nokkel(butikknummer)` |
| `fb__slv__produkt` | `kvitteringslinje.sku` | `product_code` | |
| `butikknummer` (BK) | `kvitteringslinje.storeId` | | `CASE WHEN sys__kildesystem = 'nettora' THEN 107 ELSE butikknummer END` |
| `linjenummer` (BK) | `lineNo` | `line_no` | |
| `salgsnummer` (BK) | `receiptNo` | `order_id` | |
| `antall` | `qty` | `quantity` | |
| `belop` | `qty`, `unitPrice`, `discount` | `quantity`, `price` | `antall * enhetspris_belop - rabatt_belop` |
| `enhetspris_belop` | `unitPrice` | `price` | |
| `medlemsnummer` | `kvittering.memberNo` | `customer_id` | |
| `rabatt_belop` | `discount` | | `coalesce(rabatt_belop, 0)` |
| `salg_dato` | `kvittering.soldAt` | `ordered_at` | `to_date(from_utc_timestamp(salg_tidspunkt, 'Europe/Oslo'))` |
| `salg_tidspunkt` | `kvittering.soldAt` | `ordered_at` | |
| `salgskanal` | `kvitteringslinje.sys__kildesystem` | `sys__kildesystem` | `CASE WHEN sys__kildesystem = 'nettora' THEN 'Nett' ELSE 'Butikk' END` |
| `varenummer` | `sku` | `product_code` | |

Alle kolonner med Beregning har et Utviklernotat. Relasjonen fra kvitteringslinjen til kvitteringen (modul 4) står som
før. Gull er ikke endret.

## Den genererte koden (svar på «Din tur» i steg 5)

Fra `databricks/pyspark/tabeller/slv__salgslinje.py`:

| Valget | Linjen |
|---|---|
| «Union av» | `rader, tidspunkter = sett_sammen_union(grener=[Gren(hovedtabell="brz__kassio__kvitteringslinje", …), Gren(hovedtabell="brz__nettora__ordrelinje", …)], …)` |
| Relasjonen til kvitteringen | `Kobling("brz__kassio__kvittering", par=[("storeId", …), ("receiptNo", …)])`, bare i den første grenen |
| `butikknummer` uten oppstrøm i nettbutikken | `"butikknummer": tom("int"),` i den andre grenen (og `"rabatt_belop": tom("decimal(10,2)"),`) |
| `nokkel(butikknummer)` | `"fb__slv__butikk": ("nokkel(butikknummer)", "bigint"),` under `beregninger` |
| `fb__slv__produkt` i begge | `nokkel_av("brz__kassio__kvitteringslinje.sku")` og `nokkel_av("brz__nettora__ordrelinje.product_code")` |

`sett_sammen_union` står i `databricks/pyspark/plattform/solv.py`. Den henter radene fra hver gren over de samme
tidspunktene, stabler dem og regner Beregning etterpå. Historikken (`lag_historikk`) er den samme som før.

## Tallene

| Hva | Forventet |
|---|---|
| `raw__nettora__ordrelinje` | 5 633 rader i 92 filer |
| `brz__nettora__ordrelinje` | 5 633 rader |
| `slv__salgslinje` | 44 245 rader (38 612 fra kassen, 5 633 fra nettbutikken) |
| Nett | 5 633 linjer, 3 740 ordrer, butikk 107, rabatt 0 |
| `gld__f__salg` | 44 245 rader, `pk__` unik |
| Omsetning | 38 178 930,35 kr, av det 4 275 322,95 kr på nett (11,2 %) |
| UTC-dato ulik salgsdato, nett | 224 linjer i 150 ordrer |

Andelen per ISO-uke:

| Uke | Butikk | Nett | Andel nett |
|---|---|---|---|
| 2026-W31 | 464 733,15 | 119 496,85 | 20,45 % |
| 2026-W32 | 2 757 849,35 | 300 721,80 | 9,83 % |
| 2026-W33 | 2 832 988,80 | 391 657,85 | 12,15 % |
| 2026-W34 | 2 607 974,10 | 384 641,40 | 12,85 % |
| 2026-W35 | 2 750 908,15 | 297 841,55 | 9,77 % |
| 2026-W36 | 2 803 080,25 | 373 253,95 | 11,75 % |
| 2026-W37 | 2 490 166,95 | 322 200,10 | 11,46 % |
| 2026-W38 | 2 283 898,80 | 271 868,30 | 10,64 % |
| 2026-W39 | 2 284 906,60 | 310 385,35 | 11,96 % |
| 2026-W40 | 2 626 083,15 | 285 629,90 | 9,81 % |
| 2026-W41 | 2 394 531,95 | 308 529,65 | 11,41 % |
| 2026-W42 | 2 429 171,35 | 306 065,15 | 11,19 % |
| 2026-W43 | 2 619 450,75 | 284 056,05 | 9,78 % |
| 2026-W44 | 2 557 864,05 | 318 975,05 | 11,09 % |

Omsetning per butikk, varegruppe og uke, med nettbutikken, står i `fasit/fasit.json` under
`modul6_nett.omsetning_uke_butikk_varegruppe_alle`.

## Svar på «Hva tror du?» og «Tenk over»

**Kopien og `check` (steg 1).** `lint.uuid.duplicate` for tabellen og hver kolonne, 24 feil i alt: kopien har id-ene
til originalen. Kontraktens `id` øverst sjekkes ikke, men skal være det nye navnet. Når id-linjene er slettet, sier
`check` `0 feil` og tolv `lint.uuid.missing` blant advarslene. Etter `fix --add-ids --changed-from main` (eller
«Skriv nytt filformat» i steg 2, i nettlesersporet) har filen `id:` på tabellen og de elleve kolonnene, og advarslene
om manglende id er borte.

**Advarslene fra `check`.** Et vanlig kursprosjekt har rundt 150 advarsler, nesten alle om kolonner uten beskrivelse
(`lint.column.noDescription`). `0 feil` er det som teller.

**Kolonner uten verdi fra nettbutikken (steg 2).** `butikknummer`, `fb__slv__butikk` og `rabatt_belop`. Ordrelinjene har
ingen butikk (nettbutikken er butikk 107 i varesystemet), og prisen er allerede etter rabatt.

**Forhåndssjekken før «Union av» (steg 3).** Den stopper på kolonnene med to oppstrømskolonner og på manglende relasjon.
To oppstrømstabeller betyr enten «samme rad, flere tabeller» (relasjon, modul 4) eller «flere rader» (union). Bare du
vet hvilket, så du må si det på tabellen.

**Gull og nettsalget (steg 5).** Faktaen får nettsalget uten endring i gull. Det er derfor nettbutikken kom inn i sølv,
ikke som en egen fakta.

**Uke 31 (steg 6).** 1. august er en lørdag, 2. august en søndag. Butikkene er stengt på søndag (kildearket for kassen),
nettbutikken er åpen. Med én butikkdag og to nettdager blir andelen dobbelt så høy. Sammenlign derfor hele uker.

**107 i spørringen (steg 6).** Legg `salgskanal` til i `gld__f__salg` (en kopi fra `slv__salgslinje`), eller som et felt i
butikkdimensjonen. Da kan analytikerne gruppere på «Nett» og «Butikk» uten å vite nummeret. Kurset gjør ikke det, for
å vise at gull ikke trenger å endres når en ny kilde kommer inn.

**Kjøp etter midnatt (steg 7).** Nettbutikken er åpen hele døgnet, butikkene har midnattsåpning bare noen dager. Med
salgsdatoen i UTC ville 224 nettlinjer havnet på dagen før, og salget per dag ville vært feil for hver dag med
nettkjøp etter midnatt.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra forhåndssjekken på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte «Union av» | Sju linjer som `slv__salgslinje: Kolonnen salgsnummer har 2 oppstrømskolonner, men ingen Beregning, …`, to om Beregning (`… bruker «butikknummer», som ikke er en annen kolonne i slv__salgslinje. …`) og `slv__salgslinje: Oppstrømstabellen brz__nettora__ordrelinje har ingen relasjon til hovedtabellen brz__kassio__kvitteringslinje, … Skal radene fra brz__nettora__ordrelinje komme i tillegg til radene fra brz__kassio__kvitteringslinje, er tabellen en union: velg begge i «Union av».` | Uten «Union av» leser koden de to tabellene som én rad fra to tabeller, og vil ha en relasjon |
| Kopierte kontrakten uten å slette id-ene | `specly.py check`: `lint.uuid.duplicate  Tabellen raw__nettora__ordrelinje har samme id som raw__kassio__kvitteringslinje i specly/Tables/raw/raw__kassio__kvitteringslinje.odcs.yaml. Den ene er en kopi: gi kopien en ny uuid v4, og la id-en stå der den sto først. …` (og én linje per kolonne) | Specly kjenner tabeller og kolonner på id-en |
| `order_id` uten nedstrømsnavn i bronze | `slv__salgslinje: Kolonnen salgsnummer har oppstrøm brz__nettora__ordrelinje.order_id, som har nedstrømsnavnet «order_id». En kolonne heter det samme som nedstrømsnavnet, ellers synes ikke en glemt omdøping. …` | Nedstrømsnavnet sjekkes for hver gren i unionen |
| `price` som `string` i bronze | `slv__salgslinje: Kolonnen enhetspris_belop har datatypen decimal(10,2), men oppstrømskolonnen brz__nettora__ordrelinje.price har string. Over bronze har en kopi samme type som oppstrømmen; typen settes i bronze. I Specly: endre typen i bronze.` | Typen settes i bronze, også for den nye kilden |
| To oppstrømskolonner fra samme gren (for eksempel `receiptNo` fra både linjen og kvitteringen på `salgsnummer`) | `slv__salgslinje: Kolonnen salgsnummer har 2 oppstrømskolonner i grenen brz__kassio__kvitteringslinje av unionen (…). I en union har en kolonne én oppstrømskolonne per gren. …` | Én kilde per gren, ellers vet ikke koden hvilken |
| Tok bort oppstrømmen på `rabatt_belop`, men beholdt `coalesce(rabatt_belop, 0)` | `slv__salgslinje: Beregningen på rabatt_belop («coalesce(rabatt_belop, 0)») bruker «rabatt_belop», som ikke er en annen kolonne i slv__salgslinje. …` | Kolonnens egen verdi finnes bare når den har oppstrøm |

**Feil forhåndssjekken ikke ser** (prøvd med lokal Spark på en kopi av løsningen):
- **Ingen Beregning på `butikknummer`.** Nettbutikkens linjer får tomt `butikknummer`, og `fk__gld__d__butikk = -2`
  (Mangler) på alle 5 633. Spørringen med `butikknummer = 107` gir 0 kr på nett.
- **Ingen Beregning på `fb__slv__butikk`.** Nøkkelen er tom for nettbutikken, og faktaen får `-1` (Ukjent) på 5 633
  linjer, selv om `butikknummer` er 107.
- **Ingen Beregning på `rabatt_belop`.** `belop` blir tom for alle nettlinjene, og nettsalget forsvinner fra summene.
  `sum` hopper over tomme verdier uten å si fra.
- **Oppstrøm på `salg_tidspunkt` fra nettbutikken, men ikke på `salg_dato`.** Ingen feil i koden: `salg_dato` er en
  Beregning over `salg_tidspunkt`. Men `./kurs sjekk M6` melder avvik i oppstrømmen, og lineage i Specly blir ufullstendig.

## Kjente Specly-feil i denne modulen

- `specly.py fix --add-ids` stopper med «specly/.specly.json har ingen projectId» i et repo som Specly aldri har
  eksportert til. Eksporter én gang fra Specly og kjør `git pull`, eller la Specly skrive id-ene (steg 2 punkt 3).
- «Union av»: Enter i søkefeltet velger den øverste tabellen i listen, ikke den du søkte etter. Velg med musen. Viser
  listen «Ingen resultater funnet» med tomt søkefelt, skriv navnet i feltet.
- Et klikk på tabellnavnet åpner navnet for redigering. Klikk i sidepanelet til venstre når du vil ut av en celle.
- Cellen «Oppstrømskolonne» kan tegne tekst oppå tekst når en kolonne har mange kilder (`belop`). Blyanten viser dem
  ryddig.
