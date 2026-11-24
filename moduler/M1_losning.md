# Modul 1: Løsning

## Tabelltypen bronze (steg 3)

Slik står den i `specly/Config/table_types.json` i repoet ditt. Det du ser på de tre fanene i Specly («Generelt»,
«Kolonnemaler», «Metadatafelt»), er det samme som feltene her:

```json
{
  "uuid": "0647fa8a-1198-4a75-bf29-f288330cdd10",
  "name": "bronze",
  "description": "1:1 med kildetabellen: kildens kolonnenavn, rensing, datatyper, nøkkel og historikk (alltid SCD2). Ingen sammenslåing. Hver kolonne som brukes videre, har et nedstrømsnavn: navnet den får i sølv.",
  "regexPattern": "^brz__",
  "delimiter": "__",
  "order": 1,
  "columnTemplates": [
    {"name": "pk__{table_name}", "flagUuids": ["256fdbca-c359-4d1a-92f4-b82cf800392f"], "dataTypeUuid": "c7a1312b-268b-406d-9772-b7efbf27a075", "dataType": "bigint", "flags": ["PK"]},
    {"name": "bk__{table_name}", "dataTypeUuid": "c7a1312b-268b-406d-9772-b7efbf27a075", "dataType": "bigint"},
    {"name": "sys__gyldig_fra", "dataTypeUuid": "9a393942-05e8-4868-9069-fd228b276c8c", "dataType": "timestamp"},
    {"name": "sys__gyldig_til", "dataTypeUuid": "9a393942-05e8-4868-9069-fd228b276c8c", "dataType": "timestamp"},
    {"name": "sys__kildesystem", "dataTypeUuid": "fccb93b1-0493-423e-84aa-c1eb4ad1bd1a", "dataType": "string"}
  ],
  "columnFieldDefUuids": ["eb59a8f1-4a22-46b8-966b-be22ee1354e8", "8315bf1e-6c44-43dd-9d66-35be564dfd5b", "d68921e9-b40b-4567-992f-c4783f823859"],
  "columnFields": ["description", "developerNote", "rensing"],
  "metadataFieldDefUuids": [],
  "tableFields": [],
  "showDownstreamName": true,
  "disableUpstreamColumns": false
}
```

`dataTypeUuid` og `flagUuids` peker på datatypene og flagget i `datatypes.json` og `flags.json`. De er like i alle
prosjekter som har oppsettet fra Git (steg 2). Hadde du laget datatypene selv, ville også de hatt andre UUID-er.

## Svar på «Hva tror du?»

- **Steg 2:** når admin eksporterer til Git. Endringer i oppsettet står under «Admindata» i listen.
- **Steg 3, testtabellen:** tabellen får ingen type av seg selv («Ingen type»), selv om navnet passer med mønsteret.
  Velger du bronze i velgeren under navnet, lages de fem standardkolonnene med en gang («5 standardkolonner
  opprettet»). Med «Tabelltype auto-tag» får tabellen typen, og du trykker «Opprett manglende».
- **Steg 3, sammenligningen:** bare `uuid` ville vært forskjellig. Det er grunnen til at oppsettet ligger i Git.
- **Steg 5:** `businessName: produktnavn` på `VARETEKST`, fordi `odcs.json` har `columnBusinessNameSource: downstreamName`.
- **Steg 6:** `{toTable}` er navnet på tabellen relasjonen går til. Regelen er navnestandarden `fb__<tabell>` skrevet som et
  mønster.
- **Steg 8:** nei. Malen tar bare med en del: ikke flaggregler, ikke `odcs.json`, ikke feltenes ODCS-kobling, ikke
  formatfeltene på kildesystemene, ikke hvilke felt en tabelltype har, og alt får nye, tilfeldige UUID-er.

## Typiske problemer

| Du ser | Hva det betyr | Gjør |
|---|---|---|
| Testtabellen fikk ikke standardkolonnene | Typen ble gitt med auto-tag, ikke med velgeren under navnet | «Opprett manglende» på tabellen |
| «Mine endringer» på Git-siden viser noe etter modulen | Testtabellen er ikke slettet, eller du har endret noe i «Admin» | Slett testtabellen. Har du klikket i listen på fanen «Metadatafelt», sett haken tilbake slik at bronze har Beskrivelse, Utviklernotat og Rensing. Ikke eksporter før listen er tom |
| Du har laget en ny tabelltype ved et uhell | Du trykket «Opprett tabelltype» i steg 3 | Ikke eksporter. Si fra til kursholderen, så rydder dere sammen |
