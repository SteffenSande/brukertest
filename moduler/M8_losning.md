# Modul 8: Løsning

## Prosjektoppsettet (steg 2)

`specly/Config/table_types.json`, to tabelltyper får krav. Specly skriver feltets nøkkel:

| Tabelltype | `requiredFieldDefUuids` | `requiredColumnFieldDefUuids` |
|---|---|---|
| `gull dimensjon` | `["eier"]` | `["description", "klassifisering"]` |
| `gull fakta` | `["eier", "granularitet"]` | `["description", "klassifisering"]` |

Feltene selv (Eier, Klassifisering, Granularitet) og koblingene til tabelltypene finnes fra før, i prosjektoppsettet
(`specly/Config/metadata_field_definitions.json` og `table_types.json`, se [modul 1](M1.md)). I eksporten står kravet
under «ADMINDATA» som «Tabelltyper · gull dimensjon» og «Tabelltyper · gull fakta».

## Kontraktene etter modul 8

Bare gull-tabellene endres: de fire fra modul 5, og `gld__d__kunde` (modul 7, er med i `start/M8`) og
`gld__f__lagerbeholdning` (modul 11) hvis du har dem. For hver tabell: eieren som `team.name` på roten av dokumentet, og
`classification` på hver kolonne. Faktaen får i tillegg `dataGranularityDescription`. Tabeller du har laget selv,
får også beskrivelsene de manglet (steg 4e).

| Tabell | `team.name` | `offentlig` | `fortrolig` | Resten |
|---|---|---|---|---|
| `gld__d__butikk` | Salgsanalyse | `butikknavn`, `kommune`, `apnet_dato` | | `intern` |
| `gld__d__produkt` | Sortiment | `produktnavn`, `merke`, `utpris_belop`, `produktgruppekode`, `produktgruppenavn`, `hovedgruppe` | | `intern` |
| `gld__d__dato` | Dataplattform | `dato`, `ar`, `kvartal`, `maned`, `uke`, `ukedag`, `er_helligdag` | | `intern` |
| `gld__f__salg` | Salgsanalyse | | `antall`, `belop`, `enhetspris_belop`, `rabatt_belop` | `intern` |
| `gld__d__kunde` | Kundeklubben | | `medlemsnummer`, `postnummer`, `bk__gld__d__kunde` | `intern` |
| `gld__f__lagerbeholdning` | Sortiment | | | `intern` |

«Resten» betyr også standardkolonnene (`pk__`, `bk__`, `sys__kildesystem`), nøklene (`fk__`, `butikknummer`,
`varenummer`, `salgsnummer`, `linjenummer`) og kolonner som `er_aktiv` og `leverandornavn`.

`gld__f__salg`, endringene i kontrakten (utdrag, `…` er linjer som står som før):

```yaml
schema:
  - id: 53e8b479-ebef-53eb-9e3c-2fa6359614d9
    name: gld__f__salg
    properties:
      - id: …
        name: pk__gld__f__salg
        …
        classification: intern
      …
      - id: 6af6d8af-e002-5d1b-87b7-b6a7c5540daf
        name: belop
        physicalType: decimal(10,2)
        logicalType: number
        description: Beløpet for linjen med mva, etter rabatt. Negativt ved retur.
        transformSourceObjects:
          - slv__salgslinje.belop
        classification: fortrolig
      …
    description: 'Salget: én rad per varelinje på en kvittering, med produkt, butikk og dato som dimensjoner. antall, belop og rabatt_belop kan summeres. enhetspris_belop er prisen på linjen, og kan ikke summeres.'
    dataGranularityDescription: Én rad per varelinje på en kvittering. En retur er en linje med negativt antall.
    customProperties:
      - property: tableType
        value: gull fakta
team:
  name: Salgsanalyse
```

Hvor Specly setter nøklene i filen, står i `specly/AGENTS.md` («Contract key order»). En eksport fra Specly skriver
dem der, uansett hvor de står i fasit.

## Tallene

Første tall: de fire gull-tabellene fra modul 5. Andre tall: fem gull-tabeller, med `gld__d__kunde` fra modul 7
(`start/M8`, eller modul 7 gjort selv).

| Hva | Fire gull-tabeller | Fem gull-tabeller |
|---|---|---|
| Gull-tabeller med krav | 4 | 5 |
| Kolonner som får klassifisering | 41 (7 + 12 + 10 + 12) | 52 (+ 9 i kunden og 2 nye i salget) |
| `offentlig` | 16 | 16 |
| `fortrolig` | 4 | 7 |
| `intern` | 21 | 29 |
| Linjer fra forhåndssjekken i steg 3, når alle beskrivelsene finnes | 9 | 11 |
| Det samme, når tabellene du laget selv, mangler beskrivelser | 13 | 17 |
| «Avvik» på `gld__f__salg` i steg 3, med og uten beskrivelser | 14 og 26 | 16 og 30 |
| Setninger for tags i første `./kjor` (én per tabell og én per kolonne) | 45 | 57 |
| Tabelltags etter kjøringen | 8 (`eier` og `klassifisering` på fire tabeller) | 10 |
| Kolonnetags etter kjøringen | 41 | 52 |

Tabelltaggen `klassifisering`: `gld__f__salg` og `gld__d__kunde` fortrolig, de tre andre dimensjonene intern. Taggene står i
`databricks/pyspark/plattform/tags_data.py` etter `./generer`.

## Beskrivelsene

<a id="beskrivelsene"></a>Til steg 4e: beskrivelsene i fasit for de tre gull-tabellene modul 5 og 7 ber deg lage
selv. Kopier dem, eller skriv dine egne. En god beskrivelse sier hva raden eller kolonnen er, og hva som er spesielt.
`gld__d__butikk` og `gld__d__dato` kom fra kurset og har beskrivelser fra før.

**`gld__d__produkt`**

Tabellen: «Produktdimensjonen: én rad per vare, med varegruppe og leverandør på samme rad. Bare gjeldende versjon (SCD1).»

| Kolonne | Beskrivelse |
|---|---|
| `pk__gld__d__produkt` | Primærnøkkel: ett tall per rad. |
| `bk__gld__d__produkt` | Forretningsnøkkelen som hash av BK-kolonnene. Lik for alle versjoner av samme rad. |
| `varenummer` | Varenummeret uten ledende nuller. |
| `er_aktiv` | Sann når varen er aktiv. |
| `hovedgruppe` | Hovedgruppen. |
| `leverandornavn` | Navnet på leverandøren. |
| `merke` | Merket. |
| `produktgruppekode` | Koden for varegruppen varen hører til nå. |
| `produktgruppenavn` | Navnet på varegruppen. |
| `produktnavn` | Navnet på varen. |
| `utpris_belop` | Veiledende utsalgspris med mva nå, i kroner. |
| `sys__kildesystem` | Kildesystemet raden kom fra. |

**`gld__f__salg`**

Tabellen: «Salget: én rad per varelinje på en kvittering, med produkt, butikk og dato som dimensjoner. antall, belop og rabatt_belop kan summeres. enhetspris_belop er prisen på linjen, og kan ikke summeres.»

| Kolonne | Beskrivelse |
|---|---|
| `pk__gld__f__salg` | Primærnøkkel: ett tall per rad. |
| `fk__gld__d__butikk` | Butikken. -1 når butikken ikke finnes i butikkdimensjonen, -2 når den mangler. |
| `fk__gld__d__dato` | Salgsdatoen som ÅÅÅÅMMDD. -1 når datoen ikke finnes i kalenderen, -2 når den mangler. |
| `fk__gld__d__kunde` | Kunden, i versjonen som gjaldt ved slutten av salgsdagen. -1 når medlemsnummeret ikke finnes i kundeklubben, -2 når kjøpet var uten medlemskort. |
| `fk__gld__d__produkt` | Produktet. -1 når varenummeret ikke finnes i produktdimensjonen, -2 når det mangler. |
| `butikknummer` | Butikknummeret (degenerert dimensjon). Med salgsnummer og linjenummer er det den naturlige nøkkelen. |
| `linjenummer` | Linjenummeret på kvitteringen (degenerert dimensjon). |
| `salgsnummer` | Kvitteringsnummeret (degenerert dimensjon). |
| `antall` | Antall. Negativt ved retur. |
| `belop` | Beløpet for linjen med mva, etter rabatt. Negativt ved retur. |
| `enhetspris_belop` | Pris per enhet med mva da varen ble solgt, i kroner. |
| `rabatt_belop` | Rabatt på linjen i kroner. |
| `salg_dato` | Datoen for kjøpet i norsk tid. Velger versjonen av kunden. |
| `sys__kildesystem` | Kildesystemet raden kom fra. |

**`gld__d__kunde`**

Tabellen: «Kundedimensjonen: én rad per versjon av et medlem (SCD2), så faktaen kan slå opp nivået medlemmet hadde den dagen det handlet.»

| Kolonne | Beskrivelse |
|---|---|
| `pk__gld__d__kunde` | Primærnøkkel: ett tall per versjon av raden. |
| `bk__gld__d__kunde` | Forretningsnøkkelen som hash av BK-kolonnene. Lik for alle versjoner av samme rad. |
| `medlemsnummer` | Medlemsnummeret. |
| `gyldig_fra` | Når versjonen startet (UTC). |
| `gyldig_til` | Når versjonen sluttet (UTC). 9999-12-31 når den gjelder nå. |
| `innmeldt_dato` | Datoen medlemmet meldte seg inn. |
| `medlemsniva` | Nivået i kundeklubben i denne versjonen: BRONZE, SILVER eller GOLD. |
| `postnummer` | Postnummeret i denne versjonen. |
| `sys__kildesystem` | Kildesystemet raden kom fra. |

`salg_dato` og `fk__gld__d__kunde` i `gld__f__salg` kom i modul 7. Har du ikke tatt den, har du ikke kolonnene.

## Slik settes taggene

Steget etter pipelinen kjører én setning per tabell og én per kolonne som mangler taggen eller har en annen verdi:

```sql
ALTER MATERIALIZED VIEW `workspace`.`toppfart`.`gld__d__butikk`
  SET TAGS ('eier' = 'Salgsanalyse', 'klassifisering' = 'intern');
ALTER MATERIALIZED VIEW `workspace`.`toppfart`.`gld__d__butikk`
  ALTER COLUMN `butikknavn` SET TAGS ('klassifisering' = 'offentlig');
```

Første gang er det 57 setninger med fem gull-tabeller. Neste `./kjor` skriver «0 setninger for tags … (alt stod
riktig fra før)»: taggene står etter en vanlig kjøring av pipelinen.

## Svar på «Hva tror du?» og «Tenk over»

- **Steg 1:** kommentaren kommer fra beskrivelsen i Specly, via `description` i kontrakten og `comment=` / `COMMENT` i den
  genererte koden. Den har vært med siden modul 2.
- **Steg 3:** med fem gull-tabeller 11 linjer: Eier på fem tabeller, Klassifisering på fem tabeller (én linje per
  tabell) og Granularitet på faktaen. Med fire gull-tabeller: 9. Hver tabell du har laget selv uten beskrivelser, gir
  to linjer til (tabellbeskrivelsen, og én linje for kolonnene): 17 med tre slike tabeller, 13 med to.
- **Steg 4c:** prisen på én vare er offentlig (den står på hylla). Omsetningen er summen av mange rader, og sier hvor godt
  hver butikk går. Den er forretningshemmelig.
- **Steg 4d:** beskrivelsen skal si hvilke mål som kan summeres, og at `enhetspris_belop` ikke kan det (modul 5).
- **Steg 5:** `gld__f__salg` får tabelltaggen `klassifisering: fortrolig`, den strengeste blant kolonnene.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra forhåndssjekken på en kopi av fasit/M8 med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte eieren på `gld__d__butikk` | `gld__d__butikk: Tabellen mangler Eier, som er påkrevd for tabelltypen gull dimensjon. I Specly: fyll ut Eier på tabellen («Vis mer»). For mange tabeller: «Import og eksport» → «Massekjøring» → «Fyll ut et tabellfelt».` | Kravet gjelder hver tabell av typen |
| Tømte beskrivelsen av `kommune` | `gld__d__butikk: Kolonnen kommune mangler Beskrivelse, som er påkrevd for tabelltypen gull dimensjon. I Specly: fyll ut Beskrivelse på kolonnene, eller koble kolonnene til et forretningsbegrep som har teksten (modul 9).` | Uten beskrivelse ingen COMMENT |
| Tømte tabellbeskrivelsen til `gld__d__dato` | `gld__d__dato: Tabellen har ingen beskrivelse, så den får ingen COMMENT i Databricks (styring for tabelltypen gull dimensjon). I Specly: skriv beskrivelsen rett under tabellnavnet.` | Tabellbeskrivelsen kan ikke gjøres påkrevd i Specly, så forhåndssjekken krever den når tabelltypen har krav |
| Skrev klassifiseringen inn i kontrakten for hånd som `hemmelig` | `gld__f__salg: Klassifisering har en verdi som ikke er et av valgene (offentlig, intern, fortrolig): belop («hemmelig»). I Specly: velg Klassifisering fra listen.` | Bare verdiene i listen gir mening i Databricks |
| Koblet Eier til sølv også, og gjorde det påkrevd | `slv__butikk: Tabellen mangler Eier, som er påkrevd for tabelltypen sølv. …`, én linje per sølvtabell | Kravet gjelder alle tabellene av typen. Bestem bevisst hvor kravene skal gjelde |

**Unntak:** «Legg til unntak» på en tabell (regelen `field.required:eier`, med begrunnelse) gjør at både Specly og
forhåndssjekken lar tabellen være. Unntaket står i kontrakten som `customProperties` → `ruleExceptions`.

**Feil forhåndssjekken ikke ser:**
- **Feil klassifisering.** `belop` som `offentlig` er en gyldig verdi. Bare et menneske ser at den er feil. Derfor er det
  lurt at forvalteren (som kjenner dataene) klassifiserer, og at en annen ser over (et forslag, steg 6).
- **En beskrivelse som er feil**, som den om målene i `gld__f__salg`. Forhåndssjekken ser bare at det står noe.
- **En beskrivelse som bare gjentar navnet** («Kommunen.» på `kommune`). Gyldig, men lite verdt.

## Kjente Specly-feil i denne modulen

- **«Send inn» gir en rød melding om at pull requesten ikke kunne åpnes.** Specly-appen på GitHub mangler da
  rettigheten «Pull requests: Read and write». Forslaget ligger på branchen `forslag/…`. Åpne pull requesten med
  lenken i meldingen. Forslaget blir stående som «Kladd» til du forkaster det (steg 6 punkt 10).
- **Hvert trykk på «Prøv igjen» legger en tom commit på branchen.** Det endrer ikke innholdet. Trykk det ikke flere
  ganger enn du trenger.
- **Listen over endringer i pull requesten kan ha med felt du ikke har rørt.** Se på selve diffen i GitHub: den viser
  bare det du endret.
- **«Slett valgte» flytter seg** på linjen nederst når «Velg verdi…» kommer (steg 4c). Se hvor du klikker.
- **Feltet for tabellbeskrivelsen sier «(valgfri)»**, også når Beskrivelse er påkrevd for tabelltypen. Kravet i
  Specly gjelder kolonnene. Forhåndssjekken krever tabellbeskrivelsen i tillegg.
- **Matrisen i «Metadatafelt» → «Tabelltyper»** viser ODCS-feltet `properties[].customProperties` ved Beskrivelse og
  Utviklernotat. De skrives til `description` og `transformDescription` i kontrakten.
