# Modul 9: Løsning

## Begrepene

| Begrep | Datatype | Nedstrømsnavn | Forretningsbeskrivelse |
|---|---|---|---|
| Butikk | `int` | (tomt) | Et utsalgssted i Toppfart, identifisert med butikknummeret. Butikkene har numrene 101-106, og nettbutikken er butikk 107. Samme nummer i varesystemet (AKTNR) og i kassen (storeId). Butikk 107 har ingen fysisk adresse. |
| Produkt | `string` | (tomt) | En vare Toppfart selger, identifisert med varenummeret uten ledende nuller (4711). Samme nummer i varesystemet og i kassen. |
| Salgsbeløp | `decimal(10,2)` | (tomt) | Det kunden betalte for en salgslinje: antall ganger enhetspris, minus rabatt, med mva, i kroner. Negativt ved retur. |
| Medlemsnivå | `string` | (tomt) | Nivået et medlem har i kundeklubben: Bronse, Sølv eller Gull. Nivået gir rabatt, og kan endre seg over tid. |

## Reglene og kolonnene

Tallene gjelder en modell med nettbutikken (modul 6) og kundeklubben (modul 7): `start/M9`, eller din egen etter modul
2–8. Det er samme utgangspunkt som modulen bruker. Kommer du rett fra modul 5, mangler `product_code` (Produkt får 5
kolonner), og Medlemsnivå får ingen.

Alle reglene har «Match hele navnet» (`^…$`).

| Begrep | Regel | Kolonner som kobles |
|---|---|---|
| Butikk | Kolonnenavn `^butikknummer$` | `slv__butikk.butikknummer`, `slv__salgslinje.butikknummer`, `gld__d__butikk.butikknummer`, `gld__f__salg.butikknummer` |
| Butikk | Nedstrømsnavn `^butikknummer$` | `brz__kassio__kvittering.storeId`, `brz__kassio__kvitteringslinje.storeId` |
| Produkt | Kolonnenavn `^varenummer$` | `slv__produkt.varenummer`, `slv__salgslinje.varenummer`, `gld__d__produkt.varenummer` |
| Produkt | Nedstrømsnavn `^varenummer$` | `brz__varius__vare.VARENR`, `brz__kassio__kvitteringslinje.sku`, `brz__nettora__ordrelinje.product_code` |
| Salgsbeløp | Kolonnenavn `^belop$` | `slv__salgslinje.belop`, `gld__f__salg.belop` |
| Medlemsnivå | Kolonnenavn `^medlemsniva$` | `slv__kunde.medlemsniva`, `gld__d__kunde.medlemsniva` |
| Medlemsnivå | Nedstrømsnavn `^medlemsniva$` | `brz__lojal__medlem.tier` |

Ikke koblet, med vilje:
- `brz__varius__aktor.AKTNR`: nedstrømsnavnet er `aktornummer`. En aktør er en butikk eller en leverandør.
- raw-kolonnene (`storeId`, `VARENR`, `sku`): de har ikke nedstrømsnavn. Raw speiler filen.
- `fk__gld__d__butikk` og `fb__slv__butikk`: de er nøkler (hash eller `-1`/`-2`), ikke butikknummeret.

## Behold eller overskriv (steg 3 og 4)

Dialogen «Bruk regler» lister bare kolonnene som har en egen beskrivelse. En kolonne uten beskrivelse får begrepets
tekst uten spørsmål. Fra `start/M9` har alle de 17 kolonnene en beskrivelse. Har du laget sølv- og bronzetabellene
selv, spør dialogen om færre.

| Kolonne | Valg | Hvorfor |
|---|---|---|
| `gld__f__salg.butikknummer` | Behold | Beskrivelsen sier at nummeret er del av den naturlige nøkkelen i faktaen |
| de fem andre i Butikk | Overskriv | Begrepets tekst sier mer («Butikken.» sier lite) |
| de seks i Produkt | Overskriv | Kolonnene sier «Varenummeret uten ledende nuller.» Begrepet sier det samme og mer |
| de to i Salgsbeløp | Overskriv | Begrepet sier også hvordan beløpet er regnet ut |
| de tre i Medlemsnivå | Behold | Kolonnene sier hvilke verdier som står i dataene (`BRONZE`, `SILVER`, `GOLD`). Begrepet sier Bronse, Sølv eller Gull |

Dette er valgene i fasit (`./kurs til M10` gir dem). Det er ikke ett riktig svar for hver kolonne, og `./kurs sjekk`
ser ikke på beskrivelsene eller på om du valgte «Behold» eller «Overskriv». Den ser at begrepene finnes, og at de
samme kolonnene er koblet som i fasit. Det som teller, er at du vet hva som står på kolonnen før du velger. Dialogen viser ikke
teksten, så se etter i tabellen først.

## Filene i Git

`specly/Concepts/Butikk.md`, `Produkt.md`, `Salgsbelop.md` og `Medlemsniva.md`. Butikk, slik Specly skriver filen:

```markdown
---
columns:
  - exceptions:
      - downstreamName
    link: linkedWithExceptions
    path: brz__kassio__kvittering.storeId
    source: ruleBased
  - exceptions:
      - downstreamName
    link: linkedWithExceptions
    path: brz__kassio__kvitteringslinje.storeId
    source: ruleBased
  - exceptions:
      - klassifisering
    link: linkedWithExceptions
    path: gld__d__butikk.butikknummer
    source: ruleBased
  - exceptions:
      - businessDescription
      - klassifisering
    link: linkedWithExceptions
    path: gld__f__salg.butikknummer
    source: ruleBased
  - exceptions:
      - developerNote
    link: linkedWithExceptions
    path: slv__butikk.butikknummer
    source: ruleBased
  - exceptions:
      - developerNote
    link: linkedWithExceptions
    path: slv__salgslinje.butikknummer
    source: ruleBased
dataType: int
name: Butikk
rules:
  - columnNamePattern: ^butikknummer$
    matchField: columnName
    isRegex: true
    tableNamePattern: null
    …
    isActive: true
    order: 0
  - columnNamePattern: ^butikknummer$
    matchField: downstreamName
    isRegex: true
    tableNamePattern: null
    …
    isActive: true
    order: 1
uuid: <uuid fra Specly>
---
Et utsalgssted i Toppfart, identifisert med butikknummeret. Butikkene har numrene 101-106, og nettbutikken er butikk 107. Samme nummer i varesystemet (AKTNR) og i kassen (storeId). Butikk 107 har ingen fysisk adresse.
```

- Specly skriver `matchField: columnName` også på regelen for kolonnenavn. Rekkefølgen på de to reglene i filen
  varierer (`order: 1` kan stå først).
- `columns` har kolonnene som er overstyrt på minst ett felt. `exceptions` sier hvilke felt. Hvilke kolonner som står
  der, kommer an på hva de hadde fra før: eget nedstrømsnavn (bronze), eget utviklernotat (sølv) og egen klassifisering
  (gull, fra modul 8).
- Salgsbeløp har også `columns`: `slv__salgslinje.belop` (eget utviklernotat), og `gld__f__salg.belop` når den har egen
  klassifisering fra modul 8.

**Kontraktene:** bare `description` endres, på kolonnene som fikk begrepets tekst. `businessName` endres ikke:
prosjektet skriver nedstrømsnavnet der (`columnBusinessNameSource: downstreamName` i `specly/Config/odcs.json`), ikke
begrepets navn.

## Tallene

| Hva | Antall |
|---|---|
| Begreper | 4 |
| Koblede kolonner | 17 (Butikk 6, Produkt 6, Salgsbeløp 2, Medlemsnivå 3) |
| Overstyrt for beskrivelsen, med valgene over | 4 (`gld__f__salg.butikknummer` og de tre i Medlemsnivå) |
| Kolonner med begrepets beskrivelse, med valgene over | 13 |
| Kolonner som får den nye Butikk-teksten i steg 5 | 5 |
| `belop` uten «Match hele navnet» | 8 treff (`belop`, `rabatt_belop`, `enhetspris_belop` og `utpris_belop`, hver i to tabeller) |

Rett fra modul 5 (uten modul 6 og 7): 13 koblede kolonner (Butikk 6, Produkt 5, Salgsbeløp 2).

## Svar på «Hva tror du?»

- **Steg 1:** fire tabeller har `butikknummer`. Kassen kaller det `storeId`. `AKTNR` er et aktørnummer, ikke bare et
  butikknummer.
- **Steg 3:** Specly spør før en egen tekst skrives over («Behold» / «Overskriv»). En kolonne uten beskrivelse får
  begrepets tekst uten spørsmål.
- **Steg 5:** `gld__f__salg.butikknummer` fikk ikke den nye setningen, fordi den er overstyrt for beskrivelsen.
- **Steg 6:** begrepet står ikke i kontrakten. Bare den arvede teksten gjør det.

## Typiske feil

| Du gjorde | Hva som skjer | Gjør |
|---|---|---|
| Mønster `belop` uten «Match hele navnet» | 8 kolonner kobles til Salgsbeløp, også rabatten og prisene. `./kurs sjekk M9`: «6 kolonner er koblet til begrepet, men ikke i fasit» | Rett regelen. Specly fjerner regelkoblingene som ikke lenger treffer, når regelen lagres |
| Skrev nedstrømsnavn `butikk` på begrepet | Alle koblede kolonner får nedstrømsnavnet `butikk`. Kolonnene i laget etter blir omdøpt, og forhåndssjekken stopper på navnene | Tøm nedstrømsnavnet på begrepet |
| «Overskriv» på alt | `gld__f__salg.butikknummer` mister setningen om nøkkelen | Skriv den tilbake på kolonnen. Kolonnen blir overstyrt av seg selv |
| Bare regel på kolonnenavn for Butikk | `storeId` i bronze kobles ikke. `./kurs sjekk M9`: «2 kolonner er ikke koblet til begrepet» | Legg til regelen på nedstrømsnavn |
| Laget begrepene, men eksporterte ikke til Git (eller hentet ikke endringene) | `./kurs sjekk M9`: «Fant ingen begreper i specly/Concepts.» Sjekken leser Git, ikke Specly | Eksporter til Git, `git pull` (nettlesersporet: «Pull»), og sjekk på nytt |
| Lagret en regel, men lukket dialogen «Bruk regler» uten å bruke den | `./kurs sjekk M9`: «en regel treffer …, men kolonnene har verken begrepets beskrivelse eller et unntak i begrepsfilen» | «Bruk alle regler» i listen over begrepene, og eksporter til Git |
| To begreper med regler som treffer samme kolonne | Specly varsler «Regeloverlapp oppdaget» | Gjør mønstrene smalere, eller bruk «Tabellnavnmønster (regex)» |

## Kjente Specly-feil i denne modulen

- Dialogen «Bruk regler» viser ikke teksten som står på kolonnen, bare `tabell.kolonne · Forretningsbeskrivelse`. Se
  etter i tabellen før du velger «Behold» eller «Overskriv».
- «Rediger» på forretningsbeskrivelsen setter markøren først i teksten. Flytt den til slutten før du legger til en
  setning.
- Datatypen på begrepet må lagres med «Lagre» etter at du har valgt i listen. (På en kolonne lagres datatypen når du
  velger.)
- «Hent inn» etter modul 9 kan åpne konfliktsiden med konflikter på `replacedText` og `previousValues` under
  begrepene. På dem beholder du din side. Se [Konfliktsiden ved «Hent inn»](start.md#konfliktsiden).
