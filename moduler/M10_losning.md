# Modul 10: Løsning

Løsningen gjelder en modell med nettbutikken (modul 6) og kunden (modul 7): `start/M10`, eller din egen etter modul
2–9. Det er samme utgangspunkt som modulen bruker. Det som er annerledes rett fra modul 5, står nederst i neste
avsnitt.

## Dataproduktet

| Felt | Verdi |
|---|---|
| Navn | Salg |
| Beskrivelse | Salget i Toppfart på varelinjenivå, som en stjerne med produkt, butikk, dato og kunde. Svarer på omsetning og returer per butikk, varegruppe og periode. |
| Eier | Salgsanalyse |
| Tabeller | `gld__d__butikk`, `gld__d__dato`, `gld__d__kunde`, `gld__d__produkt`, `gld__f__salg` |
| Diagrammer | `Salg` |
| Forbruker | Salgsledelsen, Regnskap, Ukerapporten «Omsetning per butikk» |
| Bruk | Omsetning og returer per butikk, varegruppe og uke. |
| Begrensninger | se under |
| Status | ingen. Prosjektoppsettet har ingen dataproduktstatuser (`Config/data_product_statuses.json` er tom) |

**Begrensninger:**

> Gjelder 1. august til 31. oktober 2026. Varer som ikke finnes i varesystemet (varenummer 9999) ligger under produktet
> «Ukjent». Varegruppen er slik den er i dag, ikke slik den var da varen ble solgt. Kjøp uten medlemskort har kunden
> «Mangler» (-2). enhetspris_belop kan ikke summeres; bruk belop for omsetning. Beløpene er med mva.

Det er teksten i fasit (`./kurs til M11` gir den).

**Rett fra modul 5** (uten modul 6 og 7): tre dimensjoner og fire tabeller (ikke `gld__d__kunde`), beskrivelsen sier
«produkt, butikk og dato», begrensningene får setningen «Inneholder bare salg i butikkene.» i tillegg, og setningen om
medlemskort strykes.

## `specly/DataProducts/Salg.odps.yaml`

```yaml
apiVersion: v1.1.0
kind: DataProduct
id: Salg
name: Salg
description:
  purpose: Salget i Toppfart på varelinjenivå, som en stjerne med produkt, butikk, dato og kunde. Svarer på omsetning og returer per butikk, varegruppe og periode.
  limitations: Gjelder 1. august til 31. oktober 2026. Varer som ikke finnes i varesystemet (varenummer 9999) ligger under produktet «Ukjent». Varegruppen er slik den er i dag, ikke slik den var da varen ble solgt. Kjøp uten medlemskort har kunden «Mangler» (-2). enhetspris_belop kan ikke summeres; bruk belop for omsetning. Beløpene er med mva.
  usage: Omsetning og returer per butikk, varegruppe og uke.
team:
  name: Salgsanalyse
outputPorts:
  - name: Salg
customProperties:
  - property: speclyId
    value: <dataproduktets uuid i Specly>
  - property: tables
    value:
      - gld__d__butikk
      - gld__d__dato
      - gld__d__kunde
      - gld__d__produkt
      - gld__f__salg
  - property: diagrams
    value:
      - Salg
  - property: forbruker
    value:
      - Salgsledelsen
      - Regnskap
      - Ukerapporten «Omsetning per butikk»
```

- Ingen `status`: prosjektet har ingen dataproduktstatuser.
- Ingen `version`: ODPS-versjonen skrives bare når «Versjon» er fylt ut på dataproduktet.
- Tabellene står sortert på navn. `forbruker` står i rekkefølgen du skrev dem.
- `limitations` står uten anførselstegn når teksten ikke har kolon. Skriver du en tekst med kolon og mellomrom etter,
  setter Specly teksten i enkle anførselstegn (YAML krever det).
- `diagrams` står bare når dataproduktet har et diagram. Fasit (`./kurs til M11`) har ingen diagrammer, og da mangler
  linjene.

## Kontraktene

Hver av de fem tabellene får `dataProduct: Salg` på roten (etter `status`, før `schema`). Linjen er bare til
informasjon. Medlemskapet står i `tables` i ODPS-filen. Eksporten skriver seks filer: ODPS-filen og de fem kontraktene.

Ved versjonsfeltet på dataproduktet står «eksporteres som versjon 1.0.0» når feltet er tomt. Kurset setter ingen
versjon.

## Svar på «Hva tror du?» og «Din tur»

- **Steg 2:** «Oppstrøm (lineage)» og «Alle hopp» hadde tatt med kjeden tilbake til raw: sju tabeller
  (`slv__salgslinje`, tre bronze- og tre raw-tabeller), men ingen dimensjoner. Uten modul 6 er det fem. Et dataprodukt
  er det du leverer, ikke alt det er laget av.
- **Steg 4:** se begrensningene over. Hver setning er noe vi fant underveis: varenummer 9999, varegruppen i dag og ikke
  additiv (modul 5), kjøp uten medlemskort (modul 7), og mva.
- **Steg 5:** kontraktene får `dataProduct: Salg`, men det er bare til informasjon.

## Typiske feil

| Du gjorde | Hva som skjer | Gjør |
|---|---|---|
| La til tabeller med «Oppstrøm (lineage)», «Alle hopp» | Produktet får `slv__salgslinje` og bronze- og raw-tabellene den leser fra, men ingen dimensjoner (8 tabeller med faktaen). `./kurs sjekk M10` melder hver tabell som mangler, og hver som ikke er med i fasit | Ta dem ut: «⋯» → «Fjern fra dataprodukt». Tabellen blir værende i prosjektet |
| Valgte «Slett tabell permanent» i stedet for «Fjern fra dataprodukt» | Tabellen slettes fra hele prosjektet, med kolonner, relasjoner og lineage | Specly spør først. Si nei. Har det skjedd: hent tabellen tilbake fra Git |
| La `gld__f__salg` til i `dataProduct:` i kontrakten i Git | Ingenting skjer i Specly | Legg tabellen til i Specly. Medlemskapet står i `tables` i ODPS-filen, men se den første kjente feilen under |
| Laget dataproduktet, men eksporterte ikke til Git (eller hentet ikke endringene) | `./kurs sjekk M10`: «Dataproduktet Salg mangler: fant ikke specly/DataProducts/Salg.odps.yaml.» Sjekken leser Git, ikke Specly | Eksporter til Git, `git pull` (nettlesersporet: «Pull»), og sjekk på nytt |
| Skrev begrensninger som «Kan inneholde feil» | Forbrukeren vet ikke hva hun skal passe på | Skriv konkrete setninger, og hva hun skal gjøre i stedet |

## Kjente Specly-feil i denne modulen

<!-- OMVEI-ODPS-TABELLER start: punktet fjernes når Specly-feilen er rettet (docs/kursholder.md) -->
- En tabell som tas ut av `tables` i ODPS-filen i Git, blir stående i dataproduktet i Specly etter «Hent inn», og neste
  eksport skriver den tilbake i filen. Legg tabeller til og ta dem ut i Specly.
<!-- OMVEI-ODPS-TABELLER slutt -->
- I Oversikt står dataproduktet med fasen «Ikke på branch», og samtidig som «Live» under «Hva er live nå?».
- Begrensninger vises i en boks på tre linjer, også i Oversikt. Leseren må rulle inne i boksen.
- Linjen «Ikke konfigurert: Påkrevd, Unik mangler et koblet flagg …» under navnet gjelder bare «Last ned
  datakontrakt». Se bort fra den.
- Eieren av et dataprodukt er fritekst, uten kobling til personer eller team (Specly sin egen hjelpetekst).
- Specly har ingen egen «forbruker». Kurset bruker et egendefinert felt, som havner i `customProperties`.
