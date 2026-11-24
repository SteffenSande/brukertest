# Modul 4: Løsning

## Slik skal modellen se ut

Alle sølvtabellene har standardkolonnene `pk__<tabell>` (PK), `bk__<tabell>`, `sys__gyldig_fra`, `sys__gyldig_til`
og `sys__kildesystem`.

**`slv__butikk`** (Radfilter `AKTTYPE = 'B'`)

| Kolonne | Datatype | Flagg | Oppstrøm |
|---|---|---|---|
| `butikknummer` | int | BK, Eget navn | `brz__varius__aktor.AKTNR` |
| `butikknavn` | string | Eget navn | `brz__varius__aktor.NAVN` |
| `kommune` | string | | `brz__varius__aktor.KOMMUNE` |
| `apnet_dato` | date | | `brz__varius__aktor.AAPNET_DT` |

**`slv__leverandor`** (Radfilter `AKTTYPE = 'L'`, svar på «Din tur» i steg 2)

| Kolonne | Datatype | Flagg | Oppstrøm |
|---|---|---|---|
| `leverandornummer` | int | BK, Eget navn | `brz__varius__aktor.AKTNR` |
| `leverandornavn` | string | Eget navn | `brz__varius__aktor.NAVN` |
| `organisasjonsnummer` | string | | `brz__varius__aktor.ORGNR` |

**`slv__produkt`** og **`slv__produktgruppe`**: lagt inn av `./kurs fyll M4`. `slv__produkt` har `fb__slv__produktgruppe`
og `fb__slv__leverandor` med relasjoner, BK på `varenummer`, og `er_aktiv` (boolean) med Beregning `statuskode = 'A'`.

**`slv__salgslinje`** (i rekkefølgen «Sorter kolonner» gir, mellom `bk__slv__salgslinje` og `sys__`-kolonnene)

| Kolonne | Datatype | Flagg | Oppstrøm | Beregning |
|---|---|---|---|---|
| `fb__slv__butikk` | bigint | FK | `brz__kassio__kvitteringslinje.storeId` | |
| `fb__slv__produkt` | bigint | FK | `brz__kassio__kvitteringslinje.sku` | |
| `butikknummer` | int | BK | `brz__kassio__kvitteringslinje.storeId` | |
| `linjenummer` | int | BK | `brz__kassio__kvitteringslinje.lineNo` | |
| `salgsnummer` | string | BK | `brz__kassio__kvitteringslinje.receiptNo` | |
| `antall` | int | | `brz__kassio__kvitteringslinje.qty` | |
| `belop` | decimal(10,2) | | `qty`, `unitPrice`, `discount` i kvitteringslinjen | `antall * enhetspris_belop - rabatt_belop` |
| `enhetspris_belop` | decimal(10,2) | | `brz__kassio__kvitteringslinje.unitPrice` | |
| `medlemsnummer` | string | | `brz__kassio__kvittering.memberNo` | |
| `rabatt_belop` | decimal(10,2) | | `brz__kassio__kvitteringslinje.discount` | |
| `salg_dato` | date | | `brz__kassio__kvittering.soldAt` | `to_date(from_utc_timestamp(salg_tidspunkt, 'Europe/Oslo'))` |
| `salg_tidspunkt` | timestamp | | `brz__kassio__kvittering.soldAt` | |
| `varenummer` | string | | `brz__kassio__kvitteringslinje.sku` | |

**Relasjoner**

| Fra | Til | Kardinalitet |
|---|---|---|
| `brz__kassio__kvitteringslinje` (`storeId`, `receiptNo`) | `brz__kassio__kvittering` (`storeId`, `receiptNo`) | 0..N til 1 |
| `slv__salgslinje.fb__slv__produkt` | `slv__produkt.bk__slv__produkt` | 0..N til 0..1 |
| `slv__salgslinje.fb__slv__butikk` | `slv__butikk.bk__slv__butikk` | 0..N til 0..1 |
| `slv__produkt.fb__slv__produktgruppe` (fra `fyll`) | `slv__produktgruppe.bk__slv__produktgruppe` | 0..N til 0..1 |
| `slv__produkt.fb__slv__leverandor` (fra `fyll`) | `slv__leverandor.bk__slv__leverandor` | 0..N til 0..1 |

**Diagrammer:** `Kasse`, `Varesystem` og `Sølv`.

## Den genererte koden

Fra `databricks/pyspark/tabeller/slv__salgslinje.py`:

| Valget i Specly | Linjen |
|---|---|
| BK, første BK-kolonne fra kvitteringslinjen | `hovedtabell="brz__kassio__kvitteringslinje",` |
| Relasjonen mellom linje og hode | `Kobling("brz__kassio__kvittering", par=[("storeId", …), ("receiptNo", …)]),` |
| `fb__slv__produkt` med oppstrøm `sku` | `"fb__slv__produkt": nokkel_av("brz__kassio__kvitteringslinje.sku"),` |
| Kolonne fra hodet | `"salg_tidspunkt": kopi("brz__kassio__kvittering.soldAt"),` |
| Beregning | `"salg_dato": ("to_date(from_utc_timestamp(salg_tidspunkt, 'Europe/Oslo'))", "date"),` |
| BK-kolonnene | `nokkel=["butikknummer", "linjenummer", "salgsnummer"],` |

BK-kolonnene står i `nokkel=[…]` i den rekkefølgen de står i tabellen. Har du ikke sortert, kan din linje ha en annen
rekkefølge, for eksempel `["butikknummer", "salgsnummer", "linjenummer"]`. Da blir hash-verdiene i `bk__` og `pk__`
andre enn i fasit, men radene, koblingene og tallene er de samme, og `./kurs sjekk M4` godtar begge.

Fra `slv__butikk.py`: `radfilter="AKTTYPE = 'B'",` og `"butikknummer": kopi("brz__varius__aktor.AKTNR"),`. Flagget
«Eget navn» gir ingen linje i koden. Det sier bare til forhåndssjekken at omdøpingen er meningen.

## Tallene

| Hva | Forventet |
|---|---|
| `slv__salgslinje` | 38 612 rader |
| `slv__butikk` | 7 (seks butikker og nettbutikken) |
| `slv__leverandor` | 10 |
| `slv__produkt` | 153 rader (`count(*)`), 150 gjeldende (`WHERE sys__gyldig_til = TIMESTAMP'9999-12-31'`) |
| `slv__produktgruppe` | 12 |
| `fb__slv__produkt` uten treff | 6 linjer, varenummer `9999`, salgsdato 2026-08-14 |
| `fb__slv__butikk` uten treff | 0 |
| Lillehammer (106) | første salgsdato 2026-09-05, første `salg_tidspunkt` 2026-09-04 22:05:07 UTC, 3 497 linjer |
| Salgsdato 2026-09-12 | 521 linjer, `sys__gyldig_fra` 2026-09-14 09:30 |
| Linjer der UTC-datoen er dagen før norsk dato | 92 linjer på 44 kvitteringer |

## Svar på «Hva tror du?», «Tenk over» og «Din tur»

**Forhåndssjekken uten «Eget navn» (steg 1).** Den stopper med to linjer, én for `butikknummer` og én for `butikknavn`.
Se meldingene under. Det er meningen: forhåndssjekken kan ikke vite om en omdøping er bevisst. Flagget sier det.

**Hvordan vet koden hvordan linje og hode kobles (steg 5)?** Fra relasjonen i steg 4. Det må være nøyaktig én relasjon
mellom hovedtabellen og den andre oppstrømstabellen.

**Hvorfor `salg_dato` fra `salg_tidspunkt`, og i `Europe/Oslo` (steg 6)?** Filnavnet sier når filen kom, ikke når
salget skjedde. Filene for 12. september kom 14. september. Tidspunktet lagres i UTC, men forretningen teller
dager i norsk tid. Et kjøp 00:05 norsk tid er 22:05 eller 23:05 UTC dagen før. Det første salget på
Lillehammer ville fått datoen 4. september, før butikken åpnet.

**`varenummer` og `fb__slv__produkt` (steg 7).** Begge trengs. Hashen kobler. Nummeret viser hvilken verdi raden hadde
når koblingen ikke traff.

**`9999` (steg 9).** Linjene skal stå. Kunden betalte, og pengene er en del av omsetningen. Kastes de, blir
omsetningen for lav, og ingen ser hvorfor. I gull peker de på raden «Ukjent» (-1) i produktdimensjonen (modul 5).

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra `./generer` på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte «Eget navn» på `butikknummer` | `slv__butikk: Kolonnen butikknummer har oppstrøm brz__varius__aktor.AKTNR, som har nedstrømsnavnet «aktornummer». En kolonne heter det samme som nedstrømsnavnet, ellers synes ikke en glemt omdøping. I Specly: gi kolonnen navnet aktornummer, rett nedstrømsnavnet på brz__varius__aktor.AKTNR, eller sett flagget «Eget navn» på butikknummer når navnet skal avvike med vilje.` | Omdøping må være bevisst |
| Skrev `AKT_TYPE` i Radfilter | `slv__butikk: Radfilteret («AKT_TYPE = 'B'») bruker AKT_TYPE, som ikke finnes i oppstrømstabellene (brz__varius__aktor). I Specly: rett Radfilter.` | Radfilteret bruker kolonnenavnene i oppstrømstabellen |
| Glemte relasjonen mellom linje og hode | `slv__salgslinje: Oppstrømstabellen brz__kassio__kvittering har ingen relasjon til hovedtabellen brz__kassio__kvitteringslinje, så koden vet ikke hvordan de skal kobles (det må være nøyaktig én). I Specly: lag én relasjon mellom brz__kassio__kvittering og brz__kassio__kvitteringslinje (kolonnene som skal være like).` | Koden kobler bare langs relasjoner |
| Glemte Utviklernotat på `salg_dato` | `slv__salgslinje: Kolonnen salg_dato har Beregning, men ingen Utviklernotat som forklarer den for mennesker. I Specly: skriv forklaringen i Utviklernotat på kolonnen (koden leser det aldri).` | Utviklernotat heter `developerNote` i Specly og `transformDescription` i kontrakten |
| Skrev `soldAt` i Beregning | `slv__salgslinje: Beregningen på salg_dato («to_date(from_utc_timestamp(soldAt, 'Europe/Oslo'))») bruker «soldAt», som ikke er en annen kolonne i slv__salgslinje. I Specly: rett Beregning, eller legg til kolonnen soldAt (med oppstrøm) i tabellen.` | Beregning bruker navnene i tabellen selv |
| Laget `fb__slv__produkt` uten relasjon | `slv__salgslinje: Kolonnen fb__slv__produkt er en koblingsnøkkel, men har ingen relasjon, så koden vet ikke hva den peker på. I Specly: lag relasjonen fra fb__slv__produkt til slv__produkt.bk__slv__produkt.` | Én melding. Navnet og typen sjekkes ikke før relasjonen finnes, for det er relasjonen som gjør kolonnen til en nøkkel |
| Kalte kolonnen `salgsdato` | `slv__salgslinje: Kolonnen salgsdato er date, men navnet slutter ikke på _dato. I Specly: gi kolonnen et navn som slutter på _dato (for eksempel salg_dato for datoen et salg skjedde).` | Navnestandarden: dato slutter på `_dato`. Rett navn er `salg_dato` |
| Ga `utpris_belop` datatypen string | `slv__produkt: Kolonnen utpris_belop er et beløp, men har datatypen string, ikke decimal.` og `… har datatypen string, men oppstrømskolonnen brz__varius__vare.UTPRIS har decimal(10,2). Over bronze har en kopi samme type som oppstrømmen; typen settes i bronze. I Specly: endre typen i bronze.` | Typen settes i bronze. Navnet `_belop` krever decimal, så forslaget er ikke å sette `string` |

**Feil forhåndssjekken ikke ser:**
- **Glemt Radfilter.** Gyldig. Begge tabellene får alle 17 aktørene. Du ser det på antallet: `slv__butikk` skal ha 7.
- **Byttet `B` og `L`.** Gyldig SQL. Butikktabellen får 10 leverandører. Se på navnene.
- **`butikknummer` hentet fra `brz__kassio__kvittering.storeId`.** Gyldig. Da blir kvitteringshodet hovedtabellen, og
  koden starter fra kvitteringene i stedet for linjene. Hent nøkkelkolonnene fra kvitteringslinjen.
- **Feil kardinalitet.** Koden bruker den ikke. Den er dokumentasjon for den som leser diagrammet.
- **Feil i Beregning som er gyldig SQL**, for eksempel `antall * enhetspris_belop + rabatt_belop`. Tallene avslører
  det: omsetningen per butikk og dag stemmer ikke med `./kurs sjekk M4`.

## Kjente Specly-feil i denne modulen

- **Ikke slett en kolonne som har en relasjon, etter at den er eksportert.** Da stopper neste eksport: «Eksport
  feilet … Relasjonen … finnes verken i Git-filen eller i Specly-filen». Lager du en `fb__` feil, rett navnet og
  oppstrømmen i stedet for å slette kolonnen. Har du alt slettet den, si fra til kursholderen. Da modulen ble prøvd,
  var veien ut å angre commiten i Git (`git revert`) og pushe. Feilen er meldt til Specly.
- «Opprett relasjon» foreslår feil par mellom to bronze-tabeller (`bk__` → `pk__` i steg 4). Fra en `fb__` til en
  sølvtabell foreslår den riktig (`fb__` → `bk__`, `0..N` og `0..1`). Sjekk paret hver gang.
- `storeId` og `receiptNo` står i begge kassetabellene, og søket treffer både raw og bronze: se på tabellnavnet over
  gruppen.
- En beregnet kolonne med flere kilder lages enklest med «Opprett 1 beregnet kolonne» i «Legg til ny kolonne fra
  oppstrømstabell» (steg 6). Blyanten i «Oppstrømskolonne» tar også flere kilder, på en kolonne som finnes.
- Kolonnene i kolonnetabellen flytter seg sidelengs når en rad får «+» i «Forretningsbegrep». Se på overskriften før
  du klikker i Datatype, Beregning eller Utviklernotat.
- Tab i Utviklernotat flytter deg til Beregning i samme rad. Klikk utenfor cellen i stedet.
- Nye kolonner legges etter `sys__`-kolonnene. «Bruk regler» → «Sorter kolonner» rydder.
