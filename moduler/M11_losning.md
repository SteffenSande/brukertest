# Modul 11: Løsning

## Kimballs fire steg (steg 1)

| Steg | Svar |
|---|---|
| Prosess | Lagerbeholdningen, målt hver dag. En tilstand, ikke en hendelse |
| Granularitet | Én rad per vare, butikk og dag i kalenderen (periodisk øyeblikksbilde). Søndag har lørdagens telling |
| Dimensjoner | Produkt, butikk og dato, de samme som for salget (felles dimensjoner) |
| Mål | `antall_pa_lager` og `antall_i_bestilling`. Semi-additive: de kan summeres over varer og butikker, ikke over dager |

## Slik skal modellen se ut

**`raw__lagra__beholdning`** (raw, kildesystem `lagra`, «Unntatt fra sortering»): `whs_store` (int), `item_no` (int),
`count_date` (date), `on_hand` (int), `on_order` (int), og de fire `sys__`-kolonnene. Kildesystemet `lagra` har filformat
`parquet` og uttrekk `Fullt`. Parquet trenger ikke skilletegn eller datoformat.

Lager du raw-tabellen via Git (steg 2), er dette hele filen `specly/Tables/raw/raw__lagra__beholdning.odcs.yaml` før
`fix --add-ids` har skrevet id-ene:

```yaml
apiVersion: v3.2.0
kind: DataContract
version: 1.0.0
id: raw__lagra__beholdning
name: raw__lagra__beholdning
schema:
  - name: raw__lagra__beholdning
    physicalType: table
    logicalType: object
    properties:
      - name: whs_store
        physicalType: int
        logicalType: integer
      - name: item_no
        physicalType: int
        logicalType: integer
      - name: count_date
        physicalType: date
        logicalType: date
      - name: on_hand
        physicalType: int
        logicalType: integer
      - name: on_order
        physicalType: int
        logicalType: integer
      - name: sys__lastet_tidspunkt
        physicalType: timestamp
        logicalType: timestamp
      - name: sys__kildefil
        physicalType: string
        logicalType: string
      - name: sys__ukjente_kolonner
        physicalType: string
        logicalType: string
      - name: sys__kildesystem
        physicalType: string
        logicalType: string
    description: Beholdningen fra lagersystemet, én fil per telling, slik filene kom.
    customProperties:
      - property: tableType
        value: raw
      - property: sourceSystem
        value: lagra
      - property: excludeFromSorting
        value: true
```

**`brz__lagra__beholdning`** (bronze): kolonnene i tabellen i steg 3. BK på `item_no` og `whs_store`, ikke på
`count_date`. `item_no` er `string`.

**Fra `fyll M11`:** `slv__lagerbeholdning` (sølv, BK `butikknummer` og `varenummer`, `fb__slv__butikk` og
`fb__slv__produkt` med relasjon til `bk__` i butikk og produkt).

**`gld__f__lagerbeholdning`** (gull fakta, Faktatype «Periodisk øyeblikksbilde»): kolonnene i tabellen i steg 5. BK på
`butikknummer`, `dato` og `varenummer`. Relasjoner:

| Fra | Til | Kardinalitet |
|---|---|---|
| `fk__gld__d__butikk` | `gld__d__butikk.pk__gld__d__butikk` | 0..N til 1 |
| `fk__gld__d__dato` | `gld__d__dato.pk__gld__d__dato` | 0..N til 1 |
| `fk__gld__d__produkt` | `gld__d__produkt.pk__gld__d__produkt` | 0..N til 1 |

**Styring (steg 5b).** Eier Sortiment, klassifisering `intern` på alle kolonnene. Beskrivelsene i fasit, til å kopiere:

| Hva | Beskrivelse |
|---|---|
| Tabellen | Lagerbeholdningen som periodisk øyeblikksbilde: én rad per vare, butikk og dag i kalenderen, også søndager, med beholdningen ved slutten av dagen. Målene kan summeres over varer og butikker, men ikke over dager. |
| Granularitet | Én rad per vare, butikk og dag i kalenderen: beholdningen ved slutten av dagen. Søndag har lørdagens telling. |
| `pk__gld__f__lagerbeholdning` | Primærnøkkel: ett tall per rad. |
| `fk__gld__d__butikk` | Butikken. -1 når butikken ikke finnes i butikkdimensjonen, -2 når den mangler. |
| `fk__gld__d__dato` | Dagen som ÅÅÅÅMMDD. |
| `fk__gld__d__produkt` | Produktet. -1 når varenummeret ikke finnes i produktdimensjonen, -2 når det mangler. |
| `dato` | Dagen beholdningen gjelder, ved slutten av dagen. Fra kalenderen, så søndager er med. |
| `antall_i_bestilling` | Antall bestilt, ikke mottatt, ved slutten av dagen. Semi-additivt: summer over varer og butikker, ikke over dager. |
| `antall_pa_lager` | Antall på lager ved slutten av dagen. Semi-additivt: summer over varer og butikker, ikke over dager. |
| `telling_dato` | Datoen for tellingen raden bygger på. En søndag er det lørdagens telling. |
| `sys__kildesystem` | Kildesystemet raden kom fra. |

`butikknummer` og `varenummer` får teksten fra begrepene Butikk og Produkt når du kobler dem i steg 5 punkt 6. Fasit
har de samme tekstene. Sjekken ser ikke på beskrivelsene.

## Den genererte koden (steg 6)

Fra `databricks/pyspark/tabeller/gld__f__lagerbeholdning.py`:

| Valget | Linjen |
|---|---|
| Faktatype «Periodisk øyeblikksbilde», dagene fra `slv__dato` | `rader = oyeblikksbilde("slv__lagerbeholdning", kalender="slv__dato", dag="slv__dato.dato")` |
| `dato` og `fk__gld__d__dato` fra kalenderen | `"dato": kopi("slv__dato.dato"),` og `"fk__gld__d__dato": nokkel_av("slv__dato.dato"),` |
| BK | `med_primaernokkel(fakta, nokkel=["butikknummer", "dato", "varenummer"], tabell="gld__f__lagerbeholdning")` |

Fra `brz__lagra__beholdning.py`: `Rens("item_no", til_type="string")` (heltall til tekst) og
`nokkel=["item_no", "whs_store"]`.

## Tallene

| Hva | Forventet |
|---|---|
| `raw__lagra__beholdning` | 66 600 rader i 79 filer |
| `brz__lagra__beholdning` | 66 600 rader (én versjon per telling) |
| `gld__f__lagerbeholdning` | 77 550 rader, 92 dager, 79 tellingsdager |
| Søndager | 10 950 rader, telling fra lørdagen før på alle. De andre dagene: 66 600 rader, telling fra samme dag |
| `fk__` | aldri `-1` eller `-2` |
| Bergen sentrum, uke 40 | sum over dager 7 448, snitt 1 064, søndag 4. oktober 1 006 |
| Tomme varer | `4492` i butikk 102, 2026-09-29 til 2026-10-04 |
| På lager 31. oktober | 6 107 (101: 872, 102: 1 090, 103: 1 032, 104: 962, 105: 1 078, 106: 1 073) |

Summen per dag og butikk for hele perioden står i `fasit/fasit.json` under `modul11_lager.sum_per_dag_og_butikk`.

## Svar på «Hva tror du?» og «Tenk over»

**Søndag (steg 1).** Beholdningen ved slutten av søndagen. Butikkene er stengt, og lageret er det samme som etter
tellingen lørdag kveld.

**Rader i bronze (steg 3).** 66 600: hver telling har en ny `count_date`, så hver telling er en ny versjon.

**Forhåndssjekken uten Faktatype (steg 5).** Den sier at faktaen henter fra en annen tabell enn hovedtabellen. Det er
riktig for en transaksjon, der beskrivelser hentes via dimensjoner. Kalenderen er ikke en beskrivelse, men aksen
øyeblikksbildet tas langs. Fordi prosjektet har kravene fra modul 8, skriver den også en blokk med fem meldinger om
styring: tabellbeskrivelsen, Eier, Granularitet, 9 kolonner uten Beskrivelse og 11 uten Klassifisering. De blir borte
i steg 5b.

**Rapport for uke 40 (steg 7).** Det avhenger av spørsmålet. «Hvor mye lå på lager i snitt» er snittet, «hvor mye har vi
nå» er siste dag. Summen er aldri svaret. Skriv det i beskrivelsen av kolonnen («Semi-additivt: summer over varer og
butikker, ikke over dager»). Fasit har denne teksten i beskrivelsen av de to kolonnene, og den blir `COMMENT` i
Databricks.

**Salg og lager sammen (steg 8).** Begge faktaene har `fk__gld__d__produkt`, `fk__gld__d__butikk` og `fk__gld__d__dato`.
Summer salget per vare, butikk og dag fra `gld__f__salg`, og koble på lageret med de tre nøklene:

```sql
WITH salg AS (
  SELECT fk__gld__d__produkt, fk__gld__d__butikk, fk__gld__d__dato, sum(antall) AS solgt
  FROM gld__f__salg GROUP BY 1, 2, 3)
SELECT d.dato, l.antall_pa_lager, coalesce(s.solgt, 0) AS solgt
FROM gld__f__lagerbeholdning l
JOIN gld__d__dato d ON d.pk__gld__d__dato = l.fk__gld__d__dato
LEFT JOIN salg s ON s.fk__gld__d__produkt = l.fk__gld__d__produkt AND s.fk__gld__d__butikk = l.fk__gld__d__butikk
                AND s.fk__gld__d__dato = l.fk__gld__d__dato
WHERE l.butikknummer = 102 AND l.varenummer = '4492' AND d.dato BETWEEN DATE'2026-09-26' AND DATE'2026-10-06'
ORDER BY d.dato
```

Resultatet: tirsdag 29. september ble de tre siste solgt (lørdag 26. kom ett par i retur, `solgt = -1`). Så ble ingen
solgt før varene kom mandag 5. oktober. Summer aldri på tvers av de to faktaene før du har gruppert hver for seg: de har
ulik granularitet.

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra forhåndssjekken på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte Faktatype | `gld__f__lagerbeholdning: Faktaen henter kolonner fra slv__dato, en annen tabell enn hovedtabellen slv__lagerbeholdning. …` | Uten Faktatype er faktaen en transaksjon |
| `dato` uten BK | `gld__f__lagerbeholdning: Faktaen er et periodisk øyeblikksbilde, men ingen BK-kolonne har oppstrøm slv__dato.dato, dagen raden gjelder. I Specly: legg til en BK-kolonne av typen date med oppstrøm slv__dato.dato.` | Uten dagen i nøkkelen får alle dagene samme `pk__` |
| Hentet `ukedag` fra kalenderen | `gld__f__lagerbeholdning: Kolonnen ukedag henter slv__dato.ukedag fra kalenderen. Et periodisk øyeblikksbilde henter bare dagen (slv__dato.dato) derfra; resten kommer via fk__gld__d__dato. …` | Beskrivelser av dagen står i datodimensjonen |
| `item_no` som `int` i bronze | `slv__lagerbeholdning: Kolonnen varenummer har datatypen string, men oppstrømskolonnen brz__lagra__beholdning.item_no har int. …` | Typen settes i bronze, og nøkler må ha samme type overalt |

**Feil forhåndssjekken ikke ser:**
- **Summen over dager.** `sum(antall_pa_lager)` over en uke er gyldig SQL. Tallet er sju ganger for stort.
- **`count_date` i BK i bronze og sølv.** Gyldig, men da er hver telling en egen rad med egen `bk__`. Varen i butikken
  har ingen fast nøkkel, og ingen annen tabell kan peke på den.
- **Dagen fra tellingene i stedet for kalenderen** (for eksempel `dato` med oppstrøm i `telling_dato` og flagget «Eget
  navn», uten Faktatype). Gyldig som transaksjon, men den bygges av gjeldende versjoner: én rad per vare og butikk, med
  siste telling. Søndagene og historikken forsvinner (resonnert fra malen, ikke kjørt).

## Kjente Specly-feil i denne modulen

- «Importer fra Databricks» krever et personlig token i Specly (modul 2). Git-veien i steg 2 virker uten.
- «+ datatype» i dialogen «Opprett kolonne med oppstrøm» gjør ingenting. Sett datatypen i kolonnen «Datatype» i
  tabellen etterpå.
- «Avvik» på tabellen viser ikke at tabellbeskrivelsen mangler. Forhåndssjekken krever den likevel.
- Beskrivelsen følger ikke med når en kolonne lages fra en oppstrømskolonne. Derfor må ni kolonner i faktaen få tekst
  i steg 5b.
- Dialogen «Opprett kolonne med oppstrøm» lukker seg ikke etter «Opprett N kolonner». Trykk «Lukk».
- I dialogen «Bruk regler» kan en rad under «Kolonner som allerede er unntak» stå uten navn, bare med et punktum. Den
  kan du se bort fra.
