# Modul 2: Løsning

## Slik skal modellen se ut

Fem raw-tabeller. Kolonnene kommer fra importen. De fire siste er standardkolonnene fra tabelltypen.

| Tabell | Kildesystem | Kolonner fra kilden (alle `string`) |
|---|---|---|
| `raw__varius__vare` | varius | `VARENR`, `VARETEKST`, `VGRP`, `LEVNR`, `MERKE`, `UTPRIS`, `STATUS` |
| `raw__varius__varegruppe` | varius | `VGRP`, `VGRP_TEKST`, `HOVEDGRP` |
| `raw__varius__aktor` | varius | `AKTNR`, `AKTTYPE`, `NAVN`, `KOMMUNE`, `AAPNET_DT`, `ORGNR` |
| `raw__kassio__kvittering` | kassio | `storeId`, `receiptNo`, `soldAt`, `memberNo`, `paymentType` |
| `raw__kassio__kvitteringslinje` | kassio | `storeId`, `receiptNo`, `lineNo`, `sku`, `qty`, `unitPrice`, `discount` |

Alle fem har i tillegg `sys__lastet_tidspunkt` (timestamp), `sys__kildefil`, `sys__ukjente_kolonner` og
`sys__kildesystem` (string).

Alle fem er «Unntatt fra sortering». I kontrakten står det som `excludeFromSorting: true` under `customProperties`. Raw
skal ha kolonnene i samme rekkefølge som filen, så sorteringsreglene ikke må røre dem.

## Kildesystemene (svar på «Din tur» i steg 4)

| Felt | varius | kassio |
|---|---|---|
| Filformat | `csv` | `csv` |
| Skilletegn | `;` | `,` |
| Desimaltegn | `,` | `.` |
| Datoformat | `dd.MM.yyyy` | |
| Tidsformat | | `yyyy-MM-dd'T'HH:mm:ssX` |
| Tidssone | | `UTC` |
| Uttrekk | `Fullt` | `Endringer` |

Raw bruker bare filformat og skilletegn. Desimaltegn, dato- og tidsformat og uttrekk brukes av bronze i modul 3. Det
er greit å fylle ut alt nå, fordi det står i samme kildeark.

## Den genererte koden (svar på «Din tur» i steg 5)

Fra `databricks/pyspark/tabeller/raw__varius__vare.py`:

| Valget i Specly | Linjen |
|---|---|
| Tabelltypen raw | `GENERERT av ./generer (maler/pyspark/raw.py.j2)` øverst |
| Navnet og kildesystemet | `"varius/vare/vare_*.csv",` |
| Filformat og skilletegn | `filformat="csv",` og `skilletegn=";",` |
| Kildesystemet på hver rad | `kildesystem="varius",` |
| Kolonnene | `Kolonne("VARENR", "string", …)` osv. i `KOLONNER` |

## Tallene

| Tabell | Filer | Rader |
|---|---|---|
| `raw__varius__vare` | 3 | 450 (150 per fil) |
| `raw__varius__varegruppe` | 3 | 36 (12 per fil) |
| `raw__varius__aktor` | 3 | 50 (16, 17, 17) |
| `raw__kassio__kvittering` | 92 (13 tomme, så `count(DISTINCT sys__kildefil)` gir 79) | 19 845 |
| `raw__kassio__kvitteringslinje` | 92 (13 tomme) | 38 613 |

## Svar på «Tenk over»

**Kassefiler med 0 rader.** Butikkene har søndagsstengt. Kassen sender likevel en fil hver morgen, også når den er
tom (for eksempel `kvittering_20260803T0600.csv`, som gjelder søndag 2. august). En tom fil er et svar: «ingen salg».
En fil som mangler, er noe annet.

**Ingen fil 13. september kl. 06.** Filene for lørdag 12. september kom for sent, 14. september kl. 09.30
(`kvitteringslinje_20260914T0930.csv`, 521 linjer). Filnavnet sier når filen kom, ikke hvilken dag salget gjelder.
Derfor regnes salgsdatoen fra `soldAt` i sølv (modul 4), ikke fra filen.

**Aktør har 16 rader i første fil og 17 i de neste.** Den nye butikken på Lillehammer (106) kom inn i uttrekket 1.
september.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra `./generer` på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte kildesystemet | `raw__varius__vare: Tabellen har ikke kildesystem, så koden vet ikke filformat og tekstformat. I Specly: gi tabellen et kildesystem under «Kildesystemer» (modul 2, steg 4).` | Koden vet ikke hvordan filene ser ut |
| Glemte skilletegn på kassio | `raw__kassio__kvittering: Kildesystemet kassio leverer CSV, men har ikke skilletegn. I Specly: fyll ut Skilletegn på kildesystemet.` | CSV trenger et skilletegn |
| Kalte tabellen `raw__vare` | `raw__vare: Navnet følger ikke mønsteret raw__<kilde>__<objekt>, så koden finner ikke filene i landing. I Specly: gi tabellen riktig navn.` | Navnet er hvordan koden finner filene |
| Glemte tabelltypen | `raw__varius__vare: Tabellen har tabelltype «ingen», og malene kjenner bare raw, bronze, sølv, gull dimensjon, gull fakta. I Specly: velg tabelltype på tabellen.` | Uten tabelltype finnes ingen mal |
| Glemte «Opprett manglende» | `raw__varius__vare: Standardkolonnen sys__kildefil for tabelltypen raw mangler. I Specly: trykk «Opprett manglende» på tabellen (lager standardkolonnene som mangler).` | Standardkolonnene må finnes |

**Feil forhåndssjekken ikke ser:**
- **Feil skilletegn** (`,` i stedet for `;` for varesystemet). Forhåndssjekken ser bare at feltet er fylt ut, ikke
  at verdien er riktig. Feilen viser seg i dataene: verdiene havner i feil kolonner eller blir tomme. Se på noen rader
  i kontrollen, ikke bare på antallet.

## Kjente Specly-feil i denne modulen

- Banneret om eldre filformat og bryteren «Skriv nytt filformat» på Git-siden. La bryteren stå av. Raden er borte
  etter neste eksport.
- Det som står under «Genererte filer», har hake i listen ved hver eksport, og du må ta haken av. Er de genererte
  filene alt like i Git, finnes ikke overskriften.
- Tallene under «Mine endringer» stemmer ikke alltid med hverandre. I steg 5 sier knappen «7 endringer», og
  kvitteringen «6 filer skrevet». Begge deler er riktig: de to kildesystemene står i samme fil.
- Kortet «Standardkolonner» under «Massekjøring» kan vise «0 tabeller mangler standardkolonner» rett etter
  «Tabelltype auto-tag». Tallet er foreldet til siden lastes på nytt.
- Panelet til venstre på kildesystem-siden oppdateres ikke etter «Auto-tagg tabeller». Last siden på nytt.
- Etter «Hent inn» spør Specly om regler («Regler for det som kom inn fra Git»). Ingen regler er haket av på
  forhånd. Prosjektets regler stemmer nå med fasit, og raw er «Unntatt fra sortering», så det er trygt å kjøre dem.
  Se på forhåndsvisningen først ([Slik setter du et startpunkt](start.md#regeldialogen)).
- Spør importen fra Databricks om den skal endre tabellnavngivingen i prosjektet, lar du haken stå av.

## Typisk stopp ved første eksport

Holder Git-siden tilbake alle tabellene med «ODCS-mappingfeil» (og «to kolonner med samme navn»), har repoet ditt en
eldre `specly/Config/odcs.json`. Si fra til kursholderen.

## Typiske problemer i Databricks

| Du ser | Hva det betyr | Gjør |
|---|---|---|
| `./kjor` stopper med `SCHEMA_ALREADY_EXISTS` | Oppsettet i modul 0 ble gjort med notebooken (nettlesersporet), og nå kjører du terminalsporet. Sporene kan ikke dele et skjema | Les meldingen `./kjor` skriver under feilen. Enklest: fortsett i nettlesersporet. Se også løsningen til modul 0 |
| `kurs_generer_kjor` stopper med «Skjemaet … har allerede pipelinen «Specly-kurs toppfart» fra terminalsporet» | Du har kjørt `./kjor` i terminalen for skjemaet | Fortsett i terminalsporet |
| `kurs_sjekk` stopper med «Ingenting er sjekket. Velg modulen din …» | Feltet «Modul» står på «Velg modul». Slik er det første gang, og etter hver «Pull» | Velg `M2` i sidepanelet «Parameters» («Show parameters»), vent til «Run all» er tilbake, og kjør på nytt |
| `kurs_sjekk` melder mange avvik, som «Tabellen brz__varius__vare mangler (fasit har den)» | Feltet «Modul» står på en senere modul | Velg `M2` i sidepanelet «Parameters» («Show parameters»), og kjør på nytt |
| SQL-editoren viser en gammel spørring, med en annen katalog eller et annet skjema | Editoren åpner den spørringen du brukte sist | Lag en ny spørring (+), og velg `workspace` og `toppfart` |
