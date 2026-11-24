# Modul 5: Løsning

## Kimballs fire steg (steg 1)

| Steg | Svar |
|---|---|
| Prosess | Salg i kassen. En hendelse |
| Granularitet | Én rad per varelinje på en kvittering |
| Dimensjoner | Produkt (med varegruppe og leverandør), butikk, dato (med uke). Kvitteringsnummer og linjenummer er degenererte dimensjoner i faktaen |
| Mål | `antall`, `rabatt_belop` og `belop` er additive: de kan summeres over alle dimensjonene. `enhetspris_belop` er ikke additiv. Den står i faktaen for snitt og for å se prisen på én linje |

Returene står i den samme faktaen, med negativt `antall` og `belop`.

## Slik skal modellen se ut

Begge tabellene er sortert med «Sorter kolonner», slik tabellene i steg 2 og 3 viser.

**`gld__d__produkt`** (gull dimensjon, Historikk SCD1, BK `varenummer`): kolonnene i tabellen i steg 2.
`produktgruppenavn` og `hovedgruppe` har oppstrøm i `slv__produktgruppe`, `leverandornavn` i `slv__leverandor`.

**`gld__f__salg`** (gull fakta): kolonnene i tabellen i steg 3. BK på `butikknummer`, `salgsnummer` og
`linjenummer`. FK-flagg på de tre `fk__`-kolonnene.

**Fra `fyll M5`:** `raw__kalender__dag`, `brz__kalender__dag`, `slv__dato`, `gld__d__butikk` (BK `butikknummer`, SCD1)
og `gld__d__dato` (BK `dato`, SCD1).

**Relasjoner** (diagrammet `Salg`)

| Fra | Til | Kardinalitet |
|---|---|---|
| `gld__f__salg.fk__gld__d__produkt` | `gld__d__produkt.pk__gld__d__produkt` | 0..N til 1 |
| `gld__f__salg.fk__gld__d__butikk` | `gld__d__butikk.pk__gld__d__butikk` | 0..N til 1 |
| `gld__f__salg.fk__gld__d__dato` | `gld__d__dato.pk__gld__d__dato` | 0..N til 1 |

## Den genererte koden (svar på «Din tur» i steg 6)

Fra `databricks/pyspark/tabeller/gld__f__salg.py`:

| Valget i Specly | Linjen |
|---|---|
| Faktaen henter fra `slv__salgslinje` | `rader = gjeldende_versjoner("slv__salgslinje")` |
| Relasjonen fra `fk__gld__d__produkt` | `fakta = sla_opp_nokkel(fakta, "fk__gld__d__produkt", dimensjon="gld__d__produkt")` |
| `fk__gld__d__dato` fra `salg_dato` | `"fk__gld__d__dato": nokkel_av("slv__salgslinje.salg_dato"),` og oppslaget i `gld__d__dato` |
| BK | `med_primaernokkel(fakta, nokkel=["butikknummer", "linjenummer", "salgsnummer"], tabell="gld__f__salg")` |

Fra `gld__d__produkt.py`: `historikk="SCD1",`, `Oppslag("slv__produktgruppe", via="fb__slv__produktgruppe"),`,
`Oppslag("slv__leverandor", via="fb__slv__leverandor"),` og `return med_spesialrader(dimensjon, KOLONNER, …)`.

Fra `gld__d__dato.py` (lagt inn av `fyll`): `datonokkel_pa=True,`.

## Tallene

| Hva | Forventet |
|---|---|
| `gld__f__salg` | 38 612 rader |
| `gld__d__produkt` | 152 rader (150 varer, `-1`, `-2`) |
| `gld__d__butikk` | 9 rader (7 butikker, `-1`, `-2`) |
| `pk__gld__d__dato` for 2026-08-01 | `20260801` |
| `fk__gld__d__produkt = -1` | 6 linjer, 2 094,00 kr (varenummer `9999`, 14. august) |
| Omsetning i kassen | 33 903 607,40 kr |
| Returer | 746 linjer (1,9 %), antall -798, beløp -597 483,10 kr |

Omsetning og returer per butikk står i modulteksten, steg 7. Omsetning per butikk, varegruppe og uke for alle uker står i
`fasit/fasit.json` under `modul5_gull_salg.omsetning_uke_butikk_varegruppe_kasse`.

Omsetning per varegruppe, hele perioden:

| Varegruppe | Omsetning |
|---|---|
| FRI01 Telt og soveposer | 3 652 280,75 |
| FRI02 Staver og stavtilbehør | 2 067 491,10 |
| FRI03 Sekker | 3 197 974,90 |
| LOP01 Løpesko | 3 556 285,80 |
| LOP02 Løpeklær | 2 188 521,10 |
| LOP03 Løpetilbehør | 1 487 750,75 |
| SKI01 Langrennsski | 2 734 652,20 |
| SKI02 Skisko og bindinger | 2 535 856,00 |
| SKI03 Skismøring og tilbehør | 1 584 091,90 |
| SYK01 Sykler | 7 232 114,90 |
| SYK02 Sykkelklær | 2 174 617,70 |
| SYK03 Sykkeltilbehør | 1 489 876,30 |
| Ukjent (`-1`) | 2 094,00 |

## Svar på «Hva tror du?» og «Tenk over»

**Kardinalitet `1` (nøyaktig én) ved dimensjonen (steg 5).** Hver faktarad peker på nøyaktig én rad i dimensjonen, også
linjene med `9999`. De peker på raden «Ukjent» (`-1`). Det er derfor spesialradene finnes: en `fk__` er aldri tom.

**Nettbutikken uten omsetning (steg 7).** Faktaen har bare salget fra kassen. Nettbutikken er en egen kilde som ikke er
tatt inn ennå. I modul 6 kommer ordrelinjene fra nettbutikken inn i den samme `slv__salgslinje`, og faktaen får dem
etter neste kjøring, uten endring i gull.

**«Ukjent» i uke 33 (steg 7).** Seks linjer 14. august med varenummer `9999`, som ikke finnes i varesystemet. Beløpet
(2 094 kr) er med i omsetningen per butikk, men kan ikke plasseres i en varegruppe. Salgssjefen bør få vite at
tallene per varegruppe har en liten rest, og noen bør finne ut hva `9999` er (en feilregistrering i kassen?).

**Prisen.** Faktaen har `enhetspris_belop` fra kassen: prisen varen faktisk ble solgt for, den dagen. En linje fra
september har 1 299 kr (minus eventuell rabatt), selv om dimensjonen nå viser utpris 1 399 kr. Det er riktig:
omsetningen skal være det kundene betalte. Utprisen i dimensjonen er en beskrivelse av varen nå. `4711` har 178 linjer
før 1. oktober og 74 fra 1. oktober.

**Varegruppen.** Med SCD1 står `3178` bare i `FRI03`. Spør du om omsetningen per varegruppe i august, havner salget
av løpesekken i august under `FRI03`, selv om den var i `LOP03` da. `LOP03` ser mindre ut i august enn den var. I kassen
gjelder det 60 linjer og 78 174,80 kr (regnet fra landingsfilene, ikke fra `fasit.json`). Om det er et problem, avhenger
av spørsmålet:
- «Hvordan selger varegruppene slik de er satt sammen i dag?» SCD1 er riktig.
- «Hva solgte `LOP03` i august, slik vi rapporterte da?» Da trengs SCD2 i produktdimensjonen og «Datoeffektiv på» i
  faktaen (modul 7).

## Typiske feil, og hva forhåndssjekken sier

Meldingene er ekte. De kom fra `./generer` på en kopi av løsningen med én feil satt inn.

| Du gjorde | Meldingen | Hva det betyr |
|---|---|---|
| Glemte Historikk på `gld__d__produkt` | `gld__d__produkt: Gull-dimensjonen har ikke feltet Historikk (SCD1 eller SCD2). I Specly: velg Historikk på tabellen.` | Koden må vite SCD1 eller SCD2 |
| Valgte SCD2 på `gld__d__produkt` | `gld__d__produkt: Dimensjonen er SCD2, men har ikke kolonnen gyldig_fra. …`, det samme for `gyldig_til`, og `gld__f__salg: Kolonnen fk__gld__d__produkt peker på SCD2-dimensjonen gld__d__produkt, men har ikke «Datoeffektiv på», så koden vet ikke hvilken versjon den skal velge. I Specly: velg datokolonnen i «Datoeffektiv på» på kolonnen.` | SCD2 krever gyldighet og et datoeffektivt oppslag (modul 7) |
| Hentet `produktnavn` rett inn i faktaen | `gld__f__salg: Faktaen henter kolonner fra slv__produkt, en annen tabell enn hovedtabellen slv__salgslinje. Beskrivende kolonner fra en annen tabell hentes via en dimensjon (fk__). I Specly: hent kolonnen fra slv__salgslinje, eller via fk__ mot en dimensjon.` | Beskrivelser hører hjemme i dimensjonen |
| Glemte å døpe om `fb__slv__produkt` i faktaen | `gld__f__salg: Kolonnen fb__slv__produkt peker på gld__d__produkt.pk__gld__d__produkt. Et fb__ har hele navnet på tabellen det peker på, og peker på dens bk__. …` og `Kolonnen fb__slv__produkt er et fb__, som bare finnes i sølv. I gull peker en fk__ på en dimensjons pk__. I Specly: bruk fk__ mot dimensjonens pk__.` | I gull heter nøkkelen `fk__` pluss dimensjonens navn |
| Glemte relasjonen fra `fk__gld__d__dato` | `gld__f__salg: Kolonnen fk__gld__d__dato er en koblingsnøkkel, men har ingen relasjon, så koden vet ikke hva den peker på. I Specly: lag relasjonen fra fk__gld__d__dato til gld__d__dato.pk__gld__d__dato.` | Én melding. Uten relasjon er kolonnen bare en kopi av `salg_dato`, og navnet og typen sjekkes først når relasjonen finnes |
| Tegnet relasjonen til `slv__produkt.bk__slv__produkt` | `gld__f__salg: Kolonnen fk__gld__d__produkt peker på slv__produkt.bk__slv__produkt. Et fk__ har hele navnet på tabellen det peker på, og peker på dens pk__. …` og `… I gull fakta peker en relasjon på en gull-dimensjons pk__. I Specly: rett relasjonen.` | Fakta peker på dimensjoner, ikke på sølv |
| Skrev Beregning `statuskode = 'A'` på `er_aktiv` i dimensjonen | Tre linjer, blant dem `gld__d__produkt: Kolonnen er_aktiv har Beregning, men en dimensjon kopierer bare fra sølv. I Specly: flytt beregningen til sølv.` | Beregningen er gjort i sølv. Dimensjonen kopierer |

**Feil forhåndssjekken ikke ser:**
- **`linjenummer` uten BK.** Gyldig, men da regnes `pk__gld__f__salg` av butikk og kvittering. Linjer på samme kvittering
  får samme `pk__`. Kontroll: `SELECT count(DISTINCT pk__gld__f__salg) FROM gld__f__salg` skal være 38 612.
- **Feil kolonnepar i en relasjon** som likevel peker på riktig dimensjons `pk__`, for eksempel `fk__gld__d__produkt` med
  relasjon til `gld__d__butikk.pk__gld__d__butikk`. Forhåndssjekken sier at navnet ikke stemmer med relasjonen. Men
  har du døpt kolonnen etter relasjonen, ser den ingenting. Tallene avslører det: nesten alle linjer får `-1`.
- **`uke` fra kalenderen er ISO-uke.** 1. og 2. august 2026 er i uke 31. Regner en rapport uken selv på en annen måte
  (for eksempel uker som starter på søndag, som i mange amerikanske verktøy), blir tallene ulike. Det er derfor
  datodimensjonen finnes: uken regnes ett sted.
- **Sum av `enhetspris_belop`.** Gyldig SQL, men tallet betyr ingenting. Omsetning er `sum(belop)`.

## Kjente Specly-feil i denne modulen

- Etter «Hent inn» kan dialogen «Regler for det som kom inn fra Git» foreslå «2 nye relasjoner» fra `gld__f__salg`.
  Modulen ber deg trykke «Ikke kjør reglene» og tegne dem selv.
- «Sorter kolonner» spør først («Sortere kolonnene?»). Sorteringen kan ikke angres med Ctrl+Z, men i gull skal
  tabellene være sortert: fasit er det, og `pk__gld__f__salg` regnes av BK-kolonnene i sortert rekkefølge.
- Nye kolonner legges etter `sys__`-kolonnene til du sorterer.
- Når du klikker ut av en celle, kan siden rulle og radene flytte seg, så neste klikk havner feil. Klikk et tomt
  sted i sidepanelet til venstre mellom hver celle.
- «Opprett relasjon» foreslo riktig kolonnepar og kardinalitet (`fk__` → `pk__`, `0..N` og `1`) for alle tre
  relasjonene da modulen ble prøvd. Sjekk paret likevel.
