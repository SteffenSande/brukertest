# Notater til kursholder og kursutvikler

Dette er ikke kursmateriale. Her står det som må lages eller bekreftes før kurset holdes. Noen avsnitt sto tidligere i
løsningene til modul 0, 1 og 8. Punktene merket «natttesten» kommer fra gjennomgangen 23.–24.11.2026, der modul 0–11 ble
kontrollert mot skjermen i Specly, GitHub og Databricks.

**Før kurset, viktigst:**
- `./kurs til` kan ikke hentes inn i et prosjekt der deltakeren har laget tabellene selv: Specly stopper på «Det
  finnes allerede en tabell med navnet …». Se «Konfliktsiden: prøvd på nytt 24.11» under.

## Modul 0: ting som må bekreftes før kurset

- Notebookene (`kurs_oppsett`, `kurs_til`, `kurs_generer_kjor`, `kurs_fyll` og `kurs_sjekk`) er kjørt i Databricks
  Free. Første gang var det fra Git-mappen til utviklingsrepoet. 23.11 ble de kjørt igjen fra Git-mappen til en ny
  kopi av malrepoet: `kurs_oppsett`, `kurs_til` fasit/M2, `kurs_generer_kjor` og `kurs_sjekk` M2 ga 16 riktige.
  Notebookene ble kjørt som jobber på serverless. Ingen deltaker har klikket «Run all».
- «Commit & Push» og «Pull» fra Git-mappen er klikket gjennom 23.11.
- Terminalsporet (`./kurs oppsett`, `./kjor --full` og `./kurs sjekk M2`) er kjørt på en ny kopi 23.11. Sjekken ga 16
  riktige.
- Ikke klikket gjennom: å legge repoet til i en Specly-app som er installert fra før (GitHub krever bekreftelse med
  mobil eller passord), «Koble til repository», og første innlesing fra et nytt repo til et tomt prosjekt. Det
  gjelder modul 0, steg 4, punkt 1–4 (også dialogen «Git-integrasjon» for et prosjekt som ikke er koblet). Klikk
  gjennom steget med en ny konto før kurset.
- Natttesten: «Run all» på serverless er klikket for `kurs_generer_kjor` og `kurs_sjekk` i modulenes løp. Senere
  samme natt er alle fem kjørt med «Run all» i et eget skjema (se «Nettlesersporet kjørt i eget skjema» under).
- Ikke klikket, modul 0 steg 6: dialogen etter «Add Git credential» under «Settings» → «Linked accounts» (kontoen
  var koblet fra før), og dialogen «Create Git folder» (mappen fantes).
- Ikke kjørt, modul 0 steg 6: `gh auth login` og `databricks auth login --host … --profile kurs` (krever ny
  innlogging). `--host` er kontrollert mot hjelpeteksten i Databricks CLI v1.26. Lenkene til installasjon i «Les mer:
  installere verktøyene» er ikke åpnet.
- Ikke sett: hvordan invitasjonen til Specly kommer til deltakeren (steg 1), og GitHub-siden for appen («Settings →
  Integrations» eller «Settings → Applications» i løsningen).
- At Specly ikke tar ODCS-innstillingene fra repoet (grunnen til modul 0, steg 5), er meldt som en feil i Specly. Når
  den er rettet, trengs ikke steget.

### Sporene kan ikke blandes i samme skjema (natttesten)

- Oppsett med notebooken `kurs_oppsett`, og så `./kjor` i terminalen: `bundle deploy` feiler med
  `SCHEMA_ALREADY_EXISTS`, fordi bundelen vil lage skjemaet og volumet selv. `./kjor` og `./kurs` skriver nå en norsk
  forklaring under feilen, med de to `databricks bundle deployment bind`-kommandoene som løste det i testen (skjemaet
  og volumet bindes til bundelen, de 457 filene ble liggende, og `./kjor` gikk rent etterpå).
- Omveien er bare prøvd når notebooken kun hadde gjort oppsettet. Den er ikke prøvd når pipelinen «Specly-kurs
  toppfart (notebook)» finnes og eier tabeller. Derfor sier meldingen at den bare skal brukes når den pipelinen ikke
  finnes. Meldingen er prøvd med en etterlignet feil, ikke mot Databricks.
- Motsatt vei: `kurs_generer_kjor` og `kurs_til` stopper med en norsk melding når terminalpipelinen finnes.
  Begge stopper nå i cellen som leser feltene, før noe er generert eller endret (sett for `kurs_til` 24.11).
- En varig løsning er å la bundelen la være å eie skjemaet og volumet (`databricks.yml`), slik at begge sporene
  bruker `CREATE SCHEMA IF NOT EXISTS`. Det er ikke gjort.

### Notebookene har ingen felt før første kjøring (natttesten)

- Sett for `kurs_generer_kjor` og `kurs_sjekk` i modulenes løp. `kurs_oppsett`, `kurs_til` og `kurs_fyll` er sett
  som nye notebooker i en ny Git-mappe 24.11 (se «Nettlesersporet kjørt i eget skjema» under).
- `kurs_fyll`: standardvalget i feltet «Modul» er nå «Velg modul», som stopper notebooken uten å endre noe
  (`dbutils.notebook.exit`, samme kall som `kurs_til` bruker). Før var standarden `M4`, så første «Run all» i modul 3
  ville fylt modul 4. Kjørt i Databricks 24.11 (se «Nettlesersporet kjørt i eget skjema» under): første «Run all»
  stopper med «Ingenting er endret. Velg modulen din …» og feltet «Modul» i sidepanelet, og andre kjøring fyller.
- Feltene blir borte etter hver «Pull» i Git-mappen, ikke bare første gang (sett for `kurs_sjekk` i modul 3 og 4).
  `kurs_sjekk` kjører da med standarden `M2`. `moduler/start.md` («Notebookene etter «Pull»») og modul 3 og 4 sier
  det, og modul 5 til 11 ved sjekken til slutt. Listen i feltet «Modul» viser `M2` til `M8`. `M9` til `M11` ligger
  under kanten, og å skrive i feltet filtrerer ikke (sett i modul 11). `moduler/start.md`, modul 9 til 11 og
  notebooken sier nå at listen må rulles.
- «Run all» kan gi dialogen «Attached cluster is terminated» etter en pause (sett i modul 3–8). Veien videre står i
  `moduler/start.md`: «Cancel», «Serverless» i verktøylinjen, «Serverless», «Run all». Knappen «Select resource» i
  dialogen er en blindvei (sett i modul 7): den åpner «Attach to an existing compute resource» med «SQL Warehouse»
  valgt, og en Python-notebook kan ikke kjøre der. Da må begge dialogene lukkes med «Cancel».
- `kurs_til`: første kjøring står på `start/M4` med «Bekreft» = `nei`. Den stopper før noe endres, så lenge noe
  ville gått tapt. Går ingenting tapt, kjører den rett gjennom (modellen byttes og pipelinen bygger alt på nytt).
  `moduler/start.md` og notebooken sier det nå.

### Nettlesersporet kjørt i eget skjema (24.11, `toppfart_nett2`)

Alle fem notebookene er kjørt med «Run all» fra en ny Git-mappe, i skjemaet `toppfart_nett2`. Dette er rettet og sett
på skjermen:

- **Feltene ligger i en egen første kodecelle («Feltene») i alle fem.** En deltaker som vil ha et annet skjema enn
  `toppfart`, kjører bare den cellen med ▶, setter «Skjema», og trykker «Run all». Sett for `kurs_oppsett`,
  `kurs_generer_kjor`, `kurs_til` og `kurs_sjekk`. Modul 0 («Les mer: et annet skjema enn `toppfart`») og
  `moduler/start.md` beskriver det.
- **`kurs_fyll` får feltet «Modul».** Før ble feltet laget i samme celle som `dbutils.notebook.exit`, og da tegnet
  Databricks det aldri. Nå stopper første «Run all» på «Velg modul» med feltet i sidepanelet, og andre kjøring med
  `M5` la inn fem tabeller.
- **`kurs_til` setter «Bekreft» tilbake til `nei`** etter en vellykket kjøring (`dbutils.widgets.remove` i én celle
  og `dbutils.widgets.dropdown` i den neste; Databricks lar ikke en notebook endre verdien i et felt). Sett to
  ganger: neste kjøring viste listen igjen. Stopper en bekreftet kjøring med feil underveis, står «Bekreft» på `ja`.
- **Sperren mot terminalsporet slår til før noe endres** i `kurs_til` og `kurs_generer_kjor`. Prøvd med en tom
  pipeline med navnet «Specly-kurs toppfart_nett2»: `kurs_til` med «Bekreft» = `ja` stoppet i cellen som leser
  feltene, og modellen i `specly/` var urørt.
- **`kurs_generer_kjor` på tom modell** stopper med «Modellen har ingen tabeller ennå …» i stedet for `IndexError`.
  `./generer` skriver det samme og avslutter med kode 1, så `./kjor` stopper før utrullingen.
- **Hodelinjene Databricks legger i notebookfilene** (`# /// script`, `# [tool.databricks.environment]`,
  `# environment_version = "6"`, `# ///`, og ingen linjeskift til slutt) står nå i filene i malrepoet. Etter at alle
  fem var kjørt, sto ingen notebook som endret i Git-vinduet, og «Pull» av nye commits som endret `kurs_til.py`, gikk
  uten flettekonflikt (to ganger). Skriver Databricks en annen `environment_version` en dag, står filene som endret
  igjen: da må tallet i de fem filene oppdateres. Rediger ikke filene slik at siste linje får linjeskift.
- `kurs_sjekk` og `kurs_til` skriver resultatet i en egen siste celle, så det ikke havner nederst i en
  utskriftsboks som må rulles.
- Ikke prøvd: en deltaker som trykker «Run all» som første handling i `kurs_oppsett` (det ville laget `toppfart`
  fra nettlesersporet i en arbeidsflate der terminalsporet eier skjemaet). Kodeveien er den samme som med ▶ først.

## Modul 2: ting som må bekreftes før kurset

- **Importen fra Databricks er ikke klikket etter «Koble til Databricks».** Den krever et personlig tilgangstoken, og
  natttesten skrev ikke inn tokens. Ubekreftet i modul 2, steg 1: «Velg katalog», «Velg skjema», «Importer N
  tabeller», «Forhåndsvisning av import», haken om tabellnavngiving (modulen sier «la haken stå av»; at haken finnes,
  er lest i en kodegjennomgang), om relasjonsreglene kjøres ved importen, og hvilken status tabellene får. Klikk
  gjennom med et token før kurset.
- Ikke klikket: knappen for å lage token etter «Settings» → «Developer» → «Access tokens» → «Manage» (trolig «Generate
  new token»), og hvilken levetid og hvilket omfang som trengs.
- **CSV-omveien er prøvd.** «Importer fra CSV» med `kilder/kildetabeller_m2.csv` ga «IMPORT VELLYKKET! Importerte 5
  tabeller med 28 kolonner», og modul 2 ble fullført med 16 riktige i sjekken. Filen er laget for hånd fra kolonnene
  i kildeviewene, og må inn i `kilder/` i utviklingsrepoet for å overleve neste bygg. Den bør lages av
  `tools/kildetabeller.py`, så den ikke kan komme i utakt. Klikkene mellom «Importer fra CSV» og kvitteringen er ikke
  beskrevet i testen.
- Ikke prøvd: kortet «Standardkolonner» under «Massekjøring» som erstatning for «Opprett manglende» på hver tabell
  (kortet viste foreldet tall; rettet i Specly 24.11, ikke kontrollert på skjermen: `docs/specly-feil.md`, feil 22). «Legg til +» på kildesystem-siden er sett, ikke trykket.
- Ikke prøvd: hvordan feil skilletegn ser ut i Databricks (løsningen, «Feil forhåndssjekken ikke ser»).
- Ikke sett i natttesten: banneret «Git har filene i et eldre format» og bryteren «Skriv nytt filformat» (steg 3a,
  punkt 3). Modul 0 sier «ikke eksporter», modul 2 sier «la bryteren stå av». Det er ikke avklart hvilken som gjelder
  når.
- «Typisk stopp ved første eksport» i løsningen («ODCS-mappingfeil») gjaldt repoer med `Config/odcs.json` fra før
  Specly endret regelen for nedstrømsnavnet 22.11. Malrepoet er rettet.

## Modul 3 og 4 (natttesten)

### Konfliktsiden: prøvd på nytt 24.11, blokkene i modul 3 til 8 er tatt ut

«Hent inn» etter en ren Git-commit (`./kurs fyll`) åpnet i natttesten siden «Hent endringer fra Git» med bare falske
konflikter: 39 i modul 3, 19 i modul 4, 49 i modul 5, 6 i modul 6, 1 i modul 7, 16 i modul 8 (etter beskrivelser
skrevet i Git) og 6 ved en «Hent inn» etter modul 9. Feilen ble meldt til Specly 24.11.2026 (Devly-chat
`cmwtw5ehh000r01hzfw1rzs7l`), og Specly ble rettet flere ganger samme natt.

**Prøvd på nytt 24.11 på dagtid** i prosjektet `steffen-toppfart` på test.specly.no, med de samme kontraktene som i
natt (modellen ble satt tilbake til commiten før hver `fyll` i natttesten, og `./kurs fyll` kjørt på nytt). 17
«Hent inn» i alt:

| «Hent inn» | Konfliktsiden |
|---|---|
| `fyll M3` (tabellene fra modul 2 og 3 er laget i Specly og aldri slettet). Natt: 39 | kom ikke |
| `fyll M4`, etter en endring i Specly som var eksportert. Natt: 19 | kom ikke |
| `fyll M5`, med fem endringer i Specly som ikke var eksportert. Natt: 49 | kom ikke |
| `fyll M6` og `fyll M7`. Natt: 6 og 1 | kom ikke |
| Modellen fram til neste modul via Git (fire ganger: nye tabeller, kolonner og relasjoner) | kom ikke |
| Beskrivelser skrevet i Git på `slv__salgslinje` og `gld__d__produkt` (som modul 8 steg 4e) | kom ikke |
| Det samme på en tabell laget i Specly og eksportert like før, og på `brz__varius__vare` (gjengi-stegene i feil 13) | kom ikke |
| En ny kontraktfil rett i Git ved siden av tabellen som var laget i Specly | kom ikke |
| Modellen tilbake til slutten av modul 11 via Git (109 linjer under «KOMMER INN»), og prøvetabellene slettet i Git | kom ikke |
| Samme felt endret på begge sider (beskrivelsen på `slv__salgslinje`) | kom, 1 ekte konflikt på `description`. Riktig |
| Modellen tilbake til før `fyll M3` (Git sletter 24 tabeller, begrepene og dataproduktet) | kom, 1 falsk konflikt: `slv__butikk.butikknavn`, `metadataTextValues`, «Før: —», «min: {"beregning": ""}», «Git: fjernet» |
| En beskrivelse skrevet i Git etter at «Gjør lik Git…» var brukt i Specly | kom, 1 falsk konflikt: `brz__varius__vare`, `description`, «Før: —», «min» en tekst Specly ikke lenger hadde, «Git» den nye teksten |

Tatt ut etter dette: blokkene `OMVEI-KONFLIKTSIDE` i `moduler/M3.md` til `M8.md`, og punktene om konfliktsiden under
«Kjente Specly-feil i denne modulen» i løsningene til modul 3 til 8. Seksjonen «Konfliktsiden ved «Hent inn»» i
`moduler/start.md` er skrevet om: den viser en ekte konflikt slik den så ut, og nevner de to tilfellene der siden
fortsatt kan komme uten at deltakeren har endret det samme feltet (startpunkt som tar bort tabeller, og modul 9).
Lenken til den i punkt 3 under «Terminalsporet» står.

**Står igjen, ikke prøvd på nytt:** blokken `OMVEI-KONFLIKTSIDE` i `moduler/M9.md` (steg 6, «Les mer: lage et begrep
i Git») og det siste punktet i løsningen til modul 9. De gjelder konfliktene på `replacedText` og `previousValues`
etter modul 9. Prøven slettet begrepene og hentet dem inn igjen fra Git, så den sier ingenting om dem.

**Det prøven ikke dekker:** tabellene i sølv og gull ble slettet fra Specly i første «Hent inn» og kom tilbake fra
Git. I natt var de laget i Specly. Bare tabellene fra modul 2 og 3 og prøvetabellen `slv__prove` var laget i Specly
da det ble hentet inn ved siden av dem. Nettlesersporet (`kurs_fyll`) er ikke prøvd.

**Nye funn i Specly fra prøven** (ikke ført i `docs/specly-feil.md`):

- **`./kurs til` lar seg ikke hente inn når deltakeren har laget tabellene selv.** Startpunktene har fasitens id-er.
  Etter `./kurs til M3` og push sto «Importer fra Git» med «Noen har pushet en endring til main i Git som Specly ikke
  kan ta inn: raw__varius__varegruppe: Det finnes allerede en tabell med navnet raw__varius__varegruppe i Specly:
  velg Git sin, Specly sin eller gi én av dem nytt navn» (én linje per raw-tabell) og «Specly står på 05cc976 til det
  er rettet i Git». Siden viste samtidig «I synk: Specly og main er like», «Sjekker Git …» gikk uten stopp, og det
  var ingen knapp for å velge. Et startpunkt virker altså bare i et prosjekt som selv kom fra et startpunkt (eller
  er tomt). `moduler/start.md` sier ikke dette.
- **Diagrammene følger ikke med tilbake.** `./kurs til` rører ikke `specly/Diagrams`. Går modellen bakover, står
  «MÅ RETTES I GIT · N FILER» under «Fra Git» («Relasjonen viser til gld__d__butikk, som ikke finnes i Git eller
  Specly») til tabellene er tilbake. «Hent inn» virker likevel.
- **Tabeller som slettes fra Git og kommer inn igjen med samme id, får stokket kolonnerekkefølge i Specly.** De sto
  straks under «Mine endringer» (`gld__d__produkt`, `gld__f__salg`, `slv__salgslinje`, senere
  `gld__f__lagerbeholdning`), sammen med diagrammene de sto i. «Forkast valgte endringer» rettet diagrammene, men
  ikke rekkefølgen. «Gjør lik Git…» rettet rekkefølgen, men avvikene kom tilbake to ganger (etter «Forkast endringer»
  på én tabell, og etter en senere «Hent inn»). Etter tredje «Gjør lik Git…» sto prosjektet «I synk» da prøven sluttet.
- **Tabellisten og tallet på dashbordet henger etter.** Etter «Hent inn» som slettet tabeller, sto de slettede
  fortsatt i «Tabeller» (24 i listen mot 12 i Git). Et klikk ga «Denne tabellen finnes ikke lenger».
- **Etter «Gjør lik Git…» regner konfliktsiden fra et gammelt utgangspunkt.** Git-siden sa «Mine endringer 0», men
  konfliktsiden viste gamle endringer under «min» (se siste rad i tabellen over). Bruker du «Gjør lik Git…» for å
  redde en deltaker, kan neste «Hent inn» gi slike konflikter. «Ta alle fra Git» er riktig da.

Modul 11 har ingen blokk. Den som sto der («Behold alle mine» ved første «Hent inn» etter `fyll M11`), var utledet og
ble aldri sett. Den er tatt ut. Kommer siden likevel i modul 11, finner deltakeren regelen via `moduler/start.md`.

Knappen heter «Hent inn til <kode>» (koden for siste commit). Natttesten så aldri «Hent inn N i Specly» og «N hentet
inn», og modulene bruker ikke de navnene lenger (rettet i modul 3–8, modul 11 og `moduler/start.md`). `./kurs fyll`,
`./kurs til` og `kurs_til` skrev «Hent inn fra branchen din». De skriver nå «Import og eksport» → «Importer fra Git» →
«Hent inn til …».

**Rådet var «Ta alle fra Git» overalt til og med modul 8. Etter modul 9 gjelder en regel med to deler** (se «Modul 9
og 10 (natttesten)» under). Sett: «Ta Git sin» på alle (modul 3), «Behold min» på alle (modul 4 og 5) og
«Behold alle mine» (modul 6) ga samme resultat etter `fyll`. «Ta alle fra Git» er trykket i modul 7 (1 konflikt etter
`fyll`: tomt `radfilter` i `tableTypeMetadata` på `slv__salgslinje`) og i modul 8 (16 konflikter etter at beskrivelser
var skrevet i kontraktfilene i Git), og virket begge ganger. I modul 8 var valget ikke likegyldig: konfliktene sto
med «Før: fantes ikke», «min: —» og «Git: <teksten>», så «Behold alle mine» ville kastet beskrivelsene. Mønsteret er
at alt som er laget i Specly, regnes som nytt på begge sider når Git endrer det (`docs/specly-feil.md`, feil 13).
Derfor sa blokkene i modul 3 til 8 «Ta alle fra Git» (de er tatt ut, se over). Konfliktsiden etter et startpunkt
er sett én gang på dagtid 24.11 (1 falsk konflikt, «Ta Git sin» virket), med modellen satt tilbake via Git, ikke
med `./kurs til`.

Meldingen «✓ Reglene er sjekket, ingen endringer» er ikke sett i noen av «Hent inn» i natttesten. Etter en ren «Hent
inn» sto det «Main står nå på <kode>» eller «Endringene fra Git er hentet», og «Reglene sjekkes når du går til
Utvikling». Modul 11 steg 4 beskriver nå det som ble sett der: «Hent inn til …», regeldialogen med en gang, og så
dialogen «Bruk regler».

### Ikke klikket eller ikke avgjort i modul 3 og 4

- **«Sorter kolonner» på sølvtabellene.** Modul 4 ber nå om sortering (steg 1, 2 og 7), så tabellene og koden blir
  lik fasit (`nokkel=["butikknummer", "linjenummer", "salgsnummer"]`). Natttesten sorterte bare bronze. Rekkefølgen
  i sølv er utledet av sorteringsreglene og fasit. Klikk gjennom én gang.
- **Eksport feiler når en eksportert kolonne med relasjon slettes** (meldt i samme Devly-chat; rettet i Specly
  24.11, ikke kontrollert på skjermen: `docs/specly-feil.md`, feil 8). Modul 4-løsningen
  ber deltakeren la være å slette, og si fra til kursholderen. Veien ut i testen var `git revert` og push. Om «slett
  relasjonen, eksporter, slett så kolonnen» virker, er ikke prøvd.
- `./kurs fyll M4` skrev «fix --apply-rules ville endret 2 kontrakter» da sølvtabellene ikke var sortert. Om
  meldingen blir borte når de er sortert, er ikke prøvd.
- Hvor knappen «+ Legg til tabeller» står i diagrammet, er ikke notert i testen. Modul 4 nevner dialogen uten sted.
- `kurs_fyll`, `kurs_til` og `kurs_generer_kjor` er ikke kjørt i nettlesersporet som en del av modul 3 og 4
  (terminalpipelinen eide skjemaet). `kurs_sjekk` er kjørt. Senere: alle fem er kjørt for seg 24.11 i `toppfart_nett2`, se «Nettlesersporet kjørt i eget skjema».
- Tiden: modul 3 står nå med 45 minutter og modul 4 med 75. Det er testagentens anslag (45–60 og 75–90), ikke målt
  med en deltaker.

## Modul 5 og 6 (natttesten)

### `specly.py fix --add-ids` virker igjen: omveien i modul 6 er tatt ut

Modul 6 steg 1 ber deltakeren kjøre `specly.py fix --add-ids --changed-from main` for å gi den kopierte kontrakten nye
id-er. Tidligere i natttesten stoppet kommandoen: «specly/.specly.json har ingen projectId, så id-ene Specly ville
laget kan ikke regnes ut.» `tools/lag_kursrepo.py` tar `projectId` ut av `specly/.specly.json` når malrepoet bygges
(med vilje), og ingen eksport skrev den inn igjen.

Specly skriver nå `projectId` ved eksport (sett i filen etter eksporten i modul 9). I testen av modul 11 virket `fix
--add-ids --changed-from main`: «fix skriver 1 fil: 1 kontrakter med nye id-er …», ti id-er på
`raw__lagra__beholdning`, og `check` hadde ingen `lint.uuid.missing` igjen for filen. Blokken `OMVEI-PROSJEKTID` er
derfor tatt ut av `moduler/M6.md`, og steg 1 punkt 4 bruker `fix --add-ids` igjen.

- **Forutsetningen står i modulen:** deltakeren må ha eksportert fra Specly minst én gang etter at prosjektet ble
  koblet til repoet, og kjørt `git pull`. `./kurs til` rører ikke `.specly.json` (`tools/kurs.py`), så id-en
  overlever et startpunkt. Den som starter på modul 6 med `./kurs til M6` rett etter modul 0, har ikke eksportert, og
  får stoppmeldingen. Modulen sier hva de gjør da.
- **Ikke sett:** `fix --add-ids` på kopien i modul 6 (tolv id-er er regnet: tabellen og elleve kolonner), og om en
  eksport uten endringer lar seg gjøre for å få `projectId` skrevet.
- **Nettlesersporet** lar fortsatt Specly skrive id-ene (modul 6 steg 2 punkt 3: «Skriv alle kontrakter på nytt…» →
  «Skriv nytt filformat»), fordi filen der committes i GitHub før noen terminal er åpnet. `fix` i «Web Terminal» er
  kjørt i modul 11, men svarte «Ingenting å rette.» (id-ene var alt skrevet), så at den skriver id-er der, er ikke
  sett. Denne veien slår på «Skriv nytt filformat», mens modul 2 sier «la bryteren stå av». I testen skrev commiten
  også `Config/metadata_field_definitions.json` og de fire diagramfilene på nytt, uten skade.
- `specly.py check` gir fortsatt rundt 150 advarsler i et vanlig kursprosjekt. Modul 6 lover `0 feil`, ikke `0
  advarsler`.

### Dobbel oppstrøm etter konfliktsiden: rettet i Specly, omveien er tatt ut

Etter «Hent fra Git» på konfliktsiden viste Specly hver oppstrømskolonne to ganger for tabeller laget i
grensesnittet, og diagramlisten viste dobbelt antall tabeller (`docs/specly-feil.md`, feil 9). Natttesten av modul 9
og 10 så at det var ryddet (`slv__salgslinje` kl. 01:57 og `gld__f__salg` kl. 02:14: én oppstrøm per kolonne, to der
kolonnen har kilde i både kasse og nett). Tatt ut: blokken `OMVEI-DOBBEL-OPPSTROM` i `moduler/M6.md` (steg 3), det
siste avsnittet i seksjonen «Konfliktsiden ved «Hent inn»» i `moduler/start.md`, og punktet i
`moduler/M6_losning.md`. Kommer feilen tilbake, ligger teksten i Git-historien. Diagramlisten er ikke kontrollert på
nytt.

### Skrevet etter lesing mot skjermen, ikke klikket

- **Modul 6 steg 3 i nettlesersporet: å redigere `slv__salgslinje.odcs.yaml` i GitHub.** Blyanten («Edit this file»)
  og dialogen «Commit changes» er sett, men de elleve linjene er ikke lagt inn den veien. Steg 1 i nettlesersporet
  («Add file» → «Create new file», lim inn, «Commit changes») er gjort på ordentlig.
- **«Web Terminal» i Git-vinduet i Databricks** er åpnet, og `python specly/.specly/specly.py check` er kjørt der
  («0 feil, 155 advarsler»). Modul 6 skriver `cd kurs-toppfart`. Mappen heter det deltakeren kalte Git-mappen.
- **`kurs_fyll`, `kurs_til` og `kurs_generer_kjor`** er ikke kjørt i nettlesersporet som en del av modul 5 og 6
  (terminalpipelinen eide skjemaet; alle fem er kjørt for seg 24.11 i `toppfart_nett2`, se «Nettlesersporet kjørt i eget skjema»). Modul 6 steg 3 sier at «Generer nå» er `kurs_generer_kjor` i nettlesersporet. Det er ikke kjørt.
- **«Kjør valgte» i regeldialogen** er ikke trykket. Modul 5 steg 4 ber deltakeren trykke «Ikke kjør reglene», som
  er trykket. Et alternativ er å la deltakeren kjøre relasjonsregelen og tegne bare den tredje relasjonen.
- **Sortering av `gld__d__produkt`** er ikke klikket. Modul 5 steg 2 ber nå om det, og tabellen i steget står i
  rekkefølgen fra fasit. `gld__f__salg` er sortert i testen og ble lik fasit.
- **At `fb__`-kolonnene står øverst i listen når `slv__salgslinje` er sortert** (modul 5 steg 3 punkt 2) er utledet
  av fasit. Testen hadde en usortert sølvtabell, og da sto de nederst.
- **De nye spørringene** i modul 5 (omsetning per butikk, nøkler med `-1`/`-2`, antall uten spesialrader) og modul 6
  (nøkler med `-1`/`-2`) er ikke kjørt slik de står. Tallene de skal gi, er sett med testagentens egne spørringer.
  Kjør dem én gang i SQL-editoren.
- **Tab i en celle med Beregning** («flytter fokus til søppelbøtta») er ikke prøvd. Setningen er tatt ut av modul 6.

### Annet fra modul 5 og 6

- Tiden: modul 5 og 6 står nå med 60 minutter hver (testagentens anslag: 55–70, ikke målt med en deltaker).
  Kjerneløpet på introsiden er 215 minutter, «ca. 3,5 timer».
- `specly.py check` gir rundt 150 advarsler om kolonner uten beskrivelse i et vanlig kursprosjekt. Modul 6 lover nå
  bare `0 feil`. Skal advarslene bort, kan `lint.column.noDescription` legges i `ignore` i `specly/.specly/check.json`
  for kurset. Ikke gjort: modul 8 handler om beskrivelser, og da er advarslene nyttige.
- `./generer` etterlater de genererte filene under `databricks/pyspark/tabeller/` ucommittet i terminalsporet
  (`tags_data.py` endret, `.gitkeep` slettet). Kurset sier ikke hva deltakeren gjør med dem. Ikke avgjort.
- `./kurs fyll` sa «Så ./kjor, og ./kurs sjekk M<n>» etter «Hent inn». I modul 5 stopper `./generer` da, fordi
  relasjonene mangler. Teksten viser nå til modulen.
- Kjent feil nr. 1 (ny kolonne og oppstrøm i samme push) lot seg ikke gjengi. Advarslene er tatt ut av modul 5 og 6.
- «Les mer: «Union av» i prosjektoppsettet» i modul 6 sa at prosjektmalen «Specly-kurs» må ha feltet. Setningen er
  tatt ut av modulen: kurset bruker ingen prosjektmal, og feltet følger med `specly/Config`.

## Modul 7 og 8 (natttesten)

### Forslag i modul 8: Specly åpner pull requesten

Avklart av Steffen 24.11: en vanlig eksport fra Specly er en commit, aldri en pull request. Forslag er unntaket:
«Send inn forslag» åpner en pull request fra Specly. (Samme dag ble pull requesten først tatt ut av forslag i Specly
#3291 etter en for bred tolkning, og lagt inn igjen i #3301.)

**Før kurset:** GitHub-appen deltakerne installerer (`specly-test-sande` på test) må ha «Pull requests: Read and
write», og installasjonene må godta den nye rettigheten. 24.11 hadde appen bare Contents og Metadata. Uten
rettigheten går alle deltakerne veien i den røde boksen i steg 6.

**Sett på test 24.11 kl. 16.45–17.00, etter Specly #3301** (prosjekt `steffen-toppfart`, appen uten rettigheten):
dialogen «Send inn forslaget» sier «Forslaget sendes til gjennomgang. Etter det kan du ikke endre det mer.» «Send
inn» ga den røde meldingen som modulen siterer, med «Åpne pull request i GitHub», «Avbryt» og «Prøv igjen».
GitHub-skjemaet var fylt ut med «Forslag: <tittel>» og listen over felt. Pull requesten ble laget og slått sammen
med `gh pr create` og `gh pr merge 3 --merge`. «Hent inn til <kode>» gikk uten konfliktside. Forslaget ble stående
som «Kladd», og «Forkast» slettet også branchen på GitHub.

**Ikke sett:** veien der Specly åpner pull requesten selv. Kvitteringen «Sendt til gjennomgang», knappen «Åpne
gjennomgangen» og statusene «Godkjent» og «Avvist» er skrevet etter tekstene i Specly-koden, ikke etter skjermen.
Gå steg 6 én gang når appen har fått rettigheten. «Create pull request», «Merge pull request» og «Confirm merge» i
GitHub i nettleseren er heller ikke trykket.

**Avvik som er meldt til Specly 24.11 (Devly-chat `cmwuvscae002t01hzm8j07gpj`):**
- Listen over endringer i forslaget hadde med tre felt ingen hadde rørt. Diffen var riktig (én linje).
- Hvert «Send inn» og «Prøv igjen» uten rettigheten la en tom commit på branchen.
- Et forslag der deltakeren åpner pull requesten selv, blir aldri «Godkjent». Det må forkastes.
- I testprosjektet sto en slettet tabell (`slv__prove`) igjen på `main` selv om Git-siden sa «I synk». Prosjektet
  hadde vært gjennom mange slettinger og id-bytter. Det er ikke prøvd i et ferskt prosjekt.

### Beskrivelsene i gull: det største hullet i modul 8, og tre måter å tette det på

En deltaker som har laget `gld__d__produkt` og `gld__f__salg` (modul 5) og `gld__d__kunde` (modul 7) selv, har ingen
beskrivelser på dem, fordi modulene ikke ber om det. Når Beskrivelse blir påkrevd i modul 8, gir forhåndssjekken 17
linjer i stedet for 11, og 35 kolonnebeskrivelser og 3 tabellbeskrivelser må skrives før steg 5 går gjennom.
Massehandlingen «Sett felt…» har bare Klassifisering. Fra `start/M8` er alt fylt ut, så bare de som har gått hele
løpet for hånd, merker det.

**Det som står i kurset nå:** modul 8 har et nytt steg 4e som sier hva som mangler, og hvordan det fylles ut i Specly
(klikk i feltet under tabellnavnet og i cellen «Beskrivelse»). Fasit-tekstene står i løsningen til å kopiere. Å
skrive dem i Git står som alternativ i en «detaljer»-boks (konfliktsiden kom ikke da det ble prøvd på nytt 24.11). Modul 7 steg 4 har
en frivillig setning om å skrive beskrivelsene der. Tallene (11, 17, 13 og 9 linjer) er kontrollert ved å kjøre
forhåndssjekken på kopier av fasit med og uten beskrivelser.

**Alternativene som ikke er valgt:**
- Be om beskrivelser i modul 5 og 7, der tabellene lages. Riktigst faglig, men gjør kjerneløpet lengre.
- La `./kurs fyll M8` (og `kurs_fyll`) legge fasit-beskrivelsene inn der de mangler. Det finnes ikke i dag: `fyll`
  kopierer bare hele kontraktfiler som mangler. Et slikt verktøy må skrive i YAML-filer Specly eier, uten å endre
  formatet, og er ikke laget eller prøvd. Testagenten gjorde det med et eget skript, og fikk 16 konflikter ved «Hent
  inn».

**Ikke prøvd:** å skrive `description`-linjene inn for hånd slik alternativet i steg 4e viser (testen brukte et
skript), og GitHub-redigering av dem i nettlesersporet.

### Tall og påstander som er regnet eller lest, ikke sett

- **«Avvik (16)» på `gld__f__salg` fra `start/M8`** og 26 fra modul 5 uten beskrivelser er regnet (Eier, Granularitet
  og én linje per kolonne og krav). Sett: «Avvik (30)» på `gld__f__salg` uten beskrivelser, og «Avvik (8)» på
  `gld__d__butikk`.
- **Tallene for fire gull-tabeller** i modul 8 steg 5 (8 tabelltags, 4/21/16 kolonner, 45 setninger for tags) er
  hentet fra fasit eller regnet. Tallene for fem (10, 7/29/16, 57) er sett.
- **Hva `kurs_generer_kjor` viser når forhåndssjekken stopper** (modul 8 steg 3) er lest i notebooken:
  `assert ok, "Forhåndssjekken stoppet. …"` i cellen under «1. Forhåndssjekk og generering». Ikke kjørt.
  `kurs_generer_kjor`, `kurs_fyll` og `kurs_til` er ikke kjørt i nettlesersporet som en del av modul 7 og 8
  (terminalpipelinen eide skjemaet). Stoppen i forhåndssjekken er heller ikke sett i kjøringen 24.11.
- **Sortering av `gld__d__kunde`** (modul 7 steg 4 punkt 5) er ikke klikket. Rekkefølgen i tabellen er fasit sin.
  Regeldialogen i modul 8 sa «Kolonnesortering – 1 tabell får ny kolonnerekkefølge» om `gld__d__kunde`, og `./kurs
  sjekk M7` godtok den usorterte tabellen.
- **«Legg til unntak»** på en avvikslinje (modul 8, «Les mer» i steg 3 og løsningen) er sett, ikke trykket.
- **Kildesystemet `lojal` har uttrekk `Fullt`** (modul 7 steg 1): står ikke på tabellsiden. Hvor det vises, er ikke
  åpnet.
- **Modul 7-løsningen, «Datoeffektiv på» på en annen dato**: at alle kjøp da blir `-1`, er resonnert fra dataene,
  ikke kjørt. Merknaden om det er tatt ut av løsningen.
- **En deltaker som går fra modul 5 rett til modul 8**: `./kurs sjekk M8` sammenligner med fasit for modul 2–8 og
  melder da tabellene fra modul 6 og 7 som avvik (kontrollert lokalt med `tools/sammenlign.py`: 24 avvik). Modul 8
  sier det. Vil dere ha en ren sjekk for den veien, må sjekken kjenne et startpunkt uten modul 6 og 7.
- **Rollene Leser og Bidragsyter** er ikke prøvd med en annen bruker. Å endre et nedstrømsnavn i et forslag er ikke
  prøvd (feltet ser redigerbart ut).

### Annet fra modul 7 og 8

- Tiden: modul 7 og 8 står nå med 45 minutter hver (testagentens anslag: 45–50, ikke målt med en deltaker). Modul 8
  sier «et kvarter til» for den som må skrive beskrivelsene. Introsiden: Admin ca. 2 t 30 min, Forvalter ca. 2 timer.
- Rettet i Specly siden kursteksten ble skrevet, og tatt ut av modulene: Eier på en tabell som finnes i Git, blir med
  i eksporten (`team.name` nederst i kontrakten). Avvik på Beskrivelse følger den innebygde beskrivelsen, og seksjonen
  «Avvik» forsvinner når alt er fylt ut. Ny kolonne og relasjon i en eksisterende tabell går i én eksport (modul 7).
  **Kommer eier-feilen tilbake**, er omveien å skrive `team:` og `  name: <eier>` nederst i hver gull-kontrakt i Git
  (uten innrykk på `team:`), pushe, «Hent inn til <kode>» og «Ta alle fra Git». Den gamle teksten ligger i
  Git-historien til `moduler/M8.md`.
- `specly/AGENTS.md` sto haket av under «Genererte filer» i eksporten i modul 8 («Speclys versjon er nyere enn den i
  Git»), og ble skrevet på nytt. Modul 8 sa «står uten hake». Den sier nå at haken står på, og at begge valg er
  ufarlige. Modul 2 ber deltakeren ta haken av. Avklar hva som er meningen.
- `kurs_sjekk` kjører med standardverdien `M2` etter hver «Pull». En deltaker som bare trykker «Run all» i modul 8,
  ser «alt grønt» uten at modul 8 er sjekket. Modul 5–8 sier at utskriften skal si «Fasittest (modul 2-N)». Notebooken
  er ikke endret: en standard som stopper («Velg modul», som i `kurs_fyll`), ville krevd ny tekst i modul 2–4.
  **Rettet 24.11:** `kurs_sjekk` har nå standarden «Velg modul» og stopper uten å sjekke noe, som `kurs_fyll`
  (feltene i første celle, `dbutils.notebook.exit` i den neste, før installasjonen). Modul 0 og 2–11 og
  `moduler/start.md` er skrevet om. Koden er kjørt lokalt med en etterligning av `dbutils`
  (`tester/test_sammenlign.py`). Den er ikke kjørt i Databricks: klikk «Run all» i en ny Git-mappe og se at feltet
  «Modul» vises etter stoppet, og at meldingen står som «Notebook exited: …».
- `./kurs fyll` og `kurs_fyll` skriver nå «(… til orientering. Du trenger ikke gjøre noe.)» etter linjen «fix
  --apply-rules ville endret N kontrakter». Ikke kjørt i Databricks.
- `./kjor` skriver alle `ALTER`-setningene for tags til skjermen (57 i modul 8). Modul 8 sier det. Vurder å skrive
  bare antallet.
- `./generer` etterlater fortsatt de genererte filene ucommittet i terminalsporet. Git-mappen i Databricks hadde ti
  ucommittede filer fra tidligere kjøringer, og «Pull» gikk likevel.
- Dobbel oppstrøm (feil 9) sto fortsatt på de gamle kolonnene i modul 7 og 8, men forstyrret ingen steg.

## Modul 9 og 10 (natttesten)

### Konfliktsiden etter modul 9: «Behold alle mine» for begrepskoblingene

En «Hent inn» etter modul 9 ga 6 konflikter, alle på `replacedText` (fem koblinger) og `previousValues` (begrepet
Butikk). Det er tekstene Specly tar vare på når en kolonne får begrepets tekst («Overskriv»), og den forrige teksten
på begrepet. De finnes bare i Specly, så «Git» er «—», og det kommer én konflikt per overskrevet kolonne ved hver
«Hent inn» (`docs/specly-feil.md`, feil 18: rettet i Specly 24.11, ikke kontrollert på skjermen etter rettelsen). Her er «Behold alle mine» riktig, altså motsatt av rådet for
endringer som kommer fra Git. `moduler/start.md` har derfor nå en regel med to deler i stedet for «Ta alle fra Git»
overalt: kom endringen fra Git, tar du Git sin; gjelder konflikten noe du gjorde i Specly, og Git-siden er tom,
beholder du din. Tabellen der har fått en fjerde rad.

- **Sett:** «Behold alle mine» → «Hent fra Git» virket, og regeldialogen kom etterpå.
- **Ikke sett:** hva «Ta alle fra Git» gjør med de lagrede tekstene (teksten i `moduler/start.md` om at den gamle
  teksten da ikke kommer tilbake, er utledet).
- **Modul 11:** første «Hent inn» etter `fyll M11` ga 0 konflikter. Konfliktene på `replacedText` og `previousValues`
  kom ikke igjen. Den utledede blokken i `moduler/M11.md` steg 4 er tatt ut.
- Omvei-blokkene i modul 3 til 8 er tatt ut (se «Konfliktsiden: prøvd på nytt 24.11»). Den som går tilbake til en
  tidligere modul etter modul 9, finner regelen i `moduler/start.md`.
- Linjen «N endringer på main» øverst i menyen under «Import og eksport» skyver «Importer fra Git» ned dit «Importer
  fra Fabric» sto. `moduler/start.md` sier det nå.

### Medlemskap i dataproduktet endret i Git: forbehold i modul 10, skal rettes tilbake

Modul 10 steg 5 sa: «Vil du legge en tabell til eller ta den ut av produktet fra Git, endrer du `tables` i
ODPS-filen, ikke kontrakten.» Testen tok `gld__d__dato` ut av `tables` i Git. Etter «Hent inn» hadde dataproduktet
fortsatt fem tabeller, «Mine endringer» viste «Salg E», og neste eksport skrev tabellen tilbake
(`docs/specly-feil.md`, feil 17: rettet i Specly 24.11, ikke kontrollert på skjermen). Setningen er byttet med «Legg tabeller til og ta dem ut i Specly, ikke i
Git». **Når feilen er rettet, rettes det tilbake:** blokken mellom `<!-- OMVEI-ODPS-TABELLER start … -->` og
`<!-- OMVEI-ODPS-TABELLER slutt -->` i `moduler/M10.md` (steg 5, svaret; den gamle setningen står i kommentaren) og i
`moduler/M10_losning.md` (første punkt under «Kjente Specly-feil», og raden om `dataProduct:` under «Typiske feil»).
**Ikke prøvd:** å legge en tabell *til* via `tables`, og det samme for et dataprodukt som kom fra Git (et startpunkt).

### Valg som er tatt i modul 9 og 10

- **Ett utgangspunkt for tallene:** modul og løsning i begge modulene regner nå fra en modell med modul 6 og 7
  (`start/M9` og `start/M10`, eller deltakerens egen etter modul 2–8). Varianten «rett fra modul 5» står én gang i
  hver fil. Tallene 17 koblede kolonner (6, 6, 2, 3), 7 tabeller ved «Oppstrøm (lineage)» og 5 tabeller i
  dataproduktet er sett.
- **«Bruk regler» med og uten beskrivelser:** dialogen lister bare kolonner som har egen beskrivelse. Testagenten
  hadde laget sølv og bronze for hånd og fikk 2 linjer ved første regel og ingen `storeId` ved den andre. Tallene for
  `start/M9` (4 linjer, og de to `storeId`) er **ikke sett**: de følger av at alle seks kolonnene har beskrivelse i
  startpunktet (kontrollert i `.startpunkter/start-M9.startpunkt`).
- **Behold eller overskriv i steg 4:** modulen og løsningen sier nå det fasit har: «Behold» på de tre kolonnene i
  Medlemsnivå, «Overskriv» på Produkt og Salgsbeløp. Begrunnelsen er at kolonnene sier `BRONZE`, `SILVER` og `GOLD`
  (verdiene i dataene), mens begrepet sier «Bronse, Sølv eller Gull». Alternativet er å skrive kodene inn i
  begrepsteksten og velge «Overskriv». Det er et faglig valg som ikke er tatt: da må begrepsteksten endres i
  `specly/Concepts/Medlemsniva.md`, modul 9 og løsningen, og startpunktene bygges på nytt.
- **Begrensningene i modul 10** er teksten fra `fasit/M10` (kontrollert mot `.startpunkter/fasit-M10.startpunkt`).
  Setningen «nettbutikken kommer med i modul 6» er ute.
- **Boksen «Kjent feil i Specly» i modul 10** (de siste 22 tegnene av Begrensninger manglet) er tatt ut. Testen skrev
  331 tegn i ett strekk, og hele teksten sto i feltet, på eksportsiden og i filen. Prøvd én gang. Modulen ber
  fortsatt deltakeren se at teksten står der til siste punktum.
- **«Ikke på branch» og «Live» i Oversikt:** modulen sier at begge betyr at dataproduktet ligger på `main` og at ingen
  branch endrer det. Det er tolket ut fra teksten på skjermen («ingen branch berører det ennå»), ikke bekreftet.
- **`./kurs sjekk M9` og `M10`** står under «Ferdig når». Fra 24.11 ser sjekken (og `kurs_sjekk`) på
  `specly/Concepts/` fra modul 9 og `specly/DataProducts/` fra modul 10 (`avvik_begreper`, `avvik_dataprodukt` og
  `sjekk_modell` i `tools/sammenlign.py`, prøvd i `tester/test_sammenlign.py`).
  - Begrepene: at de finnes, datatypen, tomt nedstrømsnavn, at de har regler, og hvilke kolonner som er koblet
    (kolonnene reglene treffer, pluss dem i `columns`, minus `link: excluded`). Ikke sammenlignet: uuid, rekkefølge,
    teksten, unntakene («Behold» eller «Overskriv», `klassifisering`) og hvor mange linjer `columns` har.
  - Dataproduktet: at det finnes, tabellene (begge veier), eier, og at Beskrivelse, Bruk, Begrensninger og Forbruker
    er fylt ut. Diagrammet kreves bare når fasit har `diagrams`. Ikke sammenlignet: `speclyId`, tekstene, status.
  - Kontrollert: fasit M9, M10 og M11 mot seg selv, og modellen fra den håndkjørte gjennomgangen (deltakerrepoet ved
    slutten av modul 11) mot fasit M11, gir 0 avvik.
  - En kobling som står i `columns` uten unntaket `businessDescription`, skal også ha begrepets tekst på kolonnen.
    Ellers meldes den (beskrivelsen på begrepet er trolig endret uten «Lagre og oppdater»).
  - Antatt, ikke sett i Specly: en regel som er lagret uten «Bruk regler», gir en kolonne som verken står i `columns`
    eller har begrepets tekst. Sjekken melder det, og meldingen sier at årsaken også kan være at beskrivelsen på
    begrepet er endret uten «Lagre og oppdater». Reglene leses med Pythons regulære uttrykk (Specly bruker Rust), og
    filtrene på en regel utenom tabellnavnmønsteret leses ikke. Kurset bruker ingen av delene.

### Ikke klikket eller ikke avgjort i modul 9 og 10

- «Bruk alle regler» og «Tagg kolonner med regler» (modul 9 steg 4) finnes med de navnene, men er ikke trykket.
  «Koble kolonne…» er trykket i et forsøk etter modulen. Å koble en overstyrt kolonne til igjen er ikke prøvd.
- Klassifisering på et begrep («Les mer: begreper og styring») er ikke prøvd.
- `fasit/M10` har ikke `diagrams` i ODPS-filen (startpunktene har ingen diagrammer). Etter `./kurs til M11` står
  dataproduktet uten diagram. Løsningen sier det.
- «Last ned datakontrakt» og «Tabellkontrakter (ZIP)» er sett, ikke trykket. «Opprett ny» diagram fra dataproduktet:
  bare dialogen er sett, ikke «Ordne» → «Arranger (relasjoner)» etterpå. Status og versjon på dataproduktet er ikke
  prøvd.
- «Vis mer · 3 felt til»: feltene sto åpne i testen (lenken het «Vis mindre»). Modulen sier «ser du dem ikke, trykk
  «Vis mer · 3 felt til»». Navnet på lenken er fra den forrige klikktesten.
- Under «Genererte filer» sto fem filer med hake i eksporten i modul 9 (`specly/AGENTS.md`, `specly/README.md`,
  `specly/.specly/specly.py` m.fl.), trolig fordi Specly ble oppdatert i løpet av natten. Sjekklisten i modul 9 sier
  «la «Genererte filer» stå som Specly foreslår», modul 2 sier «ta haken av». Samme uavklarte spørsmål som i modul 8.
- `kurs_sjekk` er kjørt i nettleseren med Modul = `M10` (dekker modul 2–10). `kurs_generer_kjor` og `kurs_til` er
  ikke kjørt i nettlesersporet som en del av modul 9 og 10 (de er kjørt for seg 24.11, se «Nettlesersporet kjørt i
  eget skjema»). `./kurs til M9`, `M10` og `M11` er ikke kjørt i denne testen av modulene, men `./kurs til` for
  M2–M11 gikk i sluttkontrollen i terminalen samme natt.
- Tiden: modul 9 står nå med 45 minutter (testagentens anslag: 40–45, ikke målt med en deltaker), modul 10 med 20
  (anslag: 20–25). Introsiden: Forvalter ca. 2 t 20 min (30 + 45 + 45 + 20).
- Doble begrepsregler etter «Hent inn» (`docs/specly-feil.md`, feil 16) ble sett i denne testen og er rettet i
  Specly 24.11. I modul 11 sto reglene 2/2/2/1 før og etter to «Hent inn» (sett kl. 02.38, før oppgaven for denne
  feilen ble startet, så rettelsen selv er ikke kontrollert på skjermen). Merknadene `OMVEI-DOBLE-REGLER` i
  `moduler/start.md`, modul 9 og modul 11 er tatt ut. Teksten ligger i Git-historien.
- `fagekspert`-feilen (`docs/specly-feil.md`, feil 2) rammer ikke kurset: prosjektoppsettet har ikke feltet. Den lot
  seg heller ikke gjengi med et midlertidig felt.

## Modul 11 (natttesten)

Modul 11 ble fullført uten omvei i terminalsporet 24.11: `./kurs sjekk M11` ga «Kontraktene stemmer med fasit.»,
«Fasittest (modul 2-11): 121 riktige, 0 feil.» og «Taggene stemmer med fasit.» `kurs_sjekk` med Modul = `M11` ga det
samme i nettleseren. Utgangspunktet var en modell laget for hånd i modul 2–10, ikke `./kurs til M11`.

### Rettet etter skjermen

- **«Hva tror du skjer?» i steg 5:** rekkefølgen er punkt 1–6, eksport, `git pull`, `./generer`, og så Faktatype.
  Utskriften har to STOPP-blokker for den som har kravene fra modul 8: 1 melding om kode og 5 om styring.
- **Steg 4:** etter regeldialogen kommer dialogen «Bruk regler» («Behold» eller «Overskriv»). Modulen sier «Behold».
- **Steg 5b:** «Avvik» viser ikke at tabellbeskrivelsen mangler, men forhåndssjekken krever den. Ni kolonner må få
  beskrivelse for hånd. Løsningen har fasit-tekstene til å kopiere.
- **Steg 9:** fem spørringer, én per rad i kontrolltabellen, med tallene fra testen.
- **Faktatype** er klikket: feltet står under «GULL FAKTA-FELT», og listen har «—», «Transaksjon» og «Periodisk
  øyeblikksbilde». «⋯» → «Unntatt fra sortering» er klikket. Boksen «Kjent feil i Specly» om «Beskrivelse er påkrevd»
  lot seg ikke gjengi, og er ute av modulen.
- **Tiden** er 60 minutter (testagentens anslag: 55–65, ikke målt med en deltaker).
- **Avslutningen** («Kurset er ferdig») er ny: hva deltakeren har bygget, hva kurset har laget i Databricks, og
  hvor man går videre.

### Ikke klikket eller ikke avgjort i modul 11

- **Veien fra modul 7 rett til modul 11 er ikke klikket.** «Start her» sier nå at den som ikke har gjort modul 8–10,
  setter startpunktet `M11`. Det er utledet av startpunktfilene: kravene (`requiredFieldDefUuids` i
  `specly/Config/table_types.json`) kommer i modul 8, og `specly/Concepts/` i modul 9. Uten dem har steg 4 ingen
  begrepsregler å kjøre, steg 5b ingenting som krever det, og `./kurs sjekk M11` sammenligner med en fasit som har
  kravene (`avvik_styring` i `tools/kurs.py`). Hva en slik deltaker faktisk ser, er ikke prøvd. `./kurs til M11` er
  heller ikke kjørt i testen.
- **Raw via Git i nettlesersporet:** i GitHub er «Add file», kopi-ikonet og «Raw» sett. «Create new file» → «Commit
  changes…» er **bare sett, ikke klikket** i modul 11 (samme dialog ble klikket i modul 6). «Pull» → «Pull anyway» og
  «Web Terminal» er klikket: terminalen starter i `/Workspace/Users/<bruker>`, så `cd kurs-toppfart` må til. `check`
  og `fix` er kjørt der, men `fix` svarte «Ingenting å rette.» Modulen lar derfor nettlesersporet få id-ene fra
  Specly (modul 6 steg 2 punkt 3), og nevner `fix` i terminalen som et forsøk.
- **Terminalvarianten av raw via Git** er gjort på ordentlig, med `raw__nettora__ordrelinje` som filen som kopieres.
  At `excludeFromSorting: true` følger med, gjelder den filen.
- **«Importer fra Databricks»** (steg 2, hovedveien) er fortsatt ikke klikket etter «Koble til Databricks» (krever
  token). «Opprett manglende» for raw er ikke sett: standardkolonnene kom av seg selv da typen ble valgt for bronze
  og gull fakta.
- **Spørring 3 i steg 9** (søndager mot andre dager i én spørring) er ikke kjørt slik den står. Testen kjørte den som
  to spørringer med `WHERE d.ukedag = 'søndag'` og `<> 'søndag'`, og fikk tallene i tabellen. Kjør den én gang i
  SQL-editoren. De fire andre er kjørt.
- **«Avvik (22)»** i steg 5b gjelder den som har koblet `butikknummer` og `varenummer` til begrepene i steg 5 punkt 6.
- **Rydding i Databricks er ikke prøvd.** Avslutningen lister det kurset har laget, hentet fra `databricks.yml`
  (skjemaet, volumet `landing` og pipelinen «Specly-kurs <skjema>»), `tools/kurspipeline.py` (pipelinen «Specly-kurs
  <skjema> (notebook)») og `tools/kildetabeller.py` (seks skjemaer `<skjema>_kilde_<kilde>`). Kurset har ingen
  kommando for å rydde, og modulen gir ingen kommandoer eller klikk for å slette. Vil dere ha det, må det prøves
  først (`databricks bundle destroy` for terminalsporet er nærliggende, men ikke kjørt).
- **Dataprodukt og diagram for den nye faktaen:** `gld__f__lagerbeholdning` står utenfor dataproduktet Salg og uten
  diagram. Modulen sier ingenting om det. Ikke avgjort.
- **Status på tabellene** («Under arbeid») endres aldri i kurset. Ikke avgjort.
- **æ, ø og å i beskrivelsescellene:** nettleserverktøyet mistet bokstavene da det skrev tegn for tegn i
  kolonnetabellen. Trolig verktøyet, ikke Specly. Skriv en beskrivelse med æ, ø og å for hånd én gang.
- **Dagen fra tellingene i stedet for kalenderen** (løsningen, «Feil forhåndssjekken ikke ser») er fortsatt resonnert
  fra malen, ikke kjørt.
- `kurs_fyll`, `kurs_generer_kjor` og `kurs_til` er ikke kjørt i nettlesersporet som en del av modul 11
  (terminalpipelinen eide skjemaet; de er kjørt for seg 24.11, se «Nettlesersporet kjørt i eget skjema»). De nye
  tekstene i `./kurs fyll`, `./kurs til` og `kurs_til` («Hent inn til …») er ikke kjørt i
  Databricks.
- Git-vinduet i Databricks hadde ti endrede filer fra tidligere kjøringer (generert kode, notebookene), alle haket
  av. Modul 11 ber deltakeren ta bort hakene før «Commit & Push» fra Git-vinduet.
- `docs/design.md` (tabellen i 7.2) er rettet 24.11 og har nå de samme tidene som modulene og introsiden.

## Modul 8: slik er taggene bygget

Dette sto før i `docs/m8-kode.md`, som var arbeidsnotatet fra da modul 8 ble bygget. Filen er tatt ut av kursrepoet
(den lå lenket fra løsningen, med branchnavn og statuslinjer som ikke stemte lenger). Den ligger i Git-historien. Det
som fortsatt gjelder:

- **COMMENT** kommer fra `description` i kontrakten: `maler/pyspark/felles_py.j2` skriver `comment=` på tabellen og
  `Kolonne(navn, type, beskrivelse)` på kolonnene. En tom beskrivelse gir `COMMENT ''`.
- **Feltene** Eier (`odcsTarget: team.name`), Klassifisering (`classification`, kan arves fra begrep) og Granularitet
  (`dataGranularityDescription`) står i `specly/Config/metadata_field_definitions.json` i alle startpunkter.
  **Kravene** (`requiredFieldDefUuids` og `requiredColumnFieldDefUuids` i `specly/Config/table_types.json`) står bare
  i fasit/M8 og senere. `tools/startpunkter.py` tar dem bort før modul 8.
- **Taggene:** `./generer` skriver `databricks/pyspark/plattform/tags_data.py` med malen `maler/pyspark/tags.py.j2`.
  Tabellen får `eier` og den strengeste klassifiseringen blant kolonnene (rekkefølgen i `dropdownOptions`), kolonnene
  får `klassifisering`. Steget etter pipelinen (`tools/sett_tags.py` i `./kjor`, `kurspipeline.sett_tags` i
  notebooken) leser først `information_schema`, og kjører bare `ALTER MATERIALIZED VIEW … SET TAGS` og `UNSET TAGS`
  for det som avviker. Bare nøklene `eier` og `klassifisering` røres.
- **Sett i natttesten:** `SET TAGS` virker på tabellene pipelinen eier (57 setninger gikk gjennom), og taggene står
  etter en vanlig kjøring («0 setninger … (alt stod riktig fra før)»). Specly eksporterer eieren som `team.name`, og
  matrisen i Admin viser ODCS-feltet `team.name` for Eier. **Ikke prøvd:** at taggene står etter en full refresh
  (`./kurs til` kjører full refresh, men setter taggene på nytt etterpå), og `UNSET TAGS` når en eier tømmes.

## Modul 1: det som må lages før kurset

### Modul 1 er en lesemodul inntil startpunktet `start/M1` finnes

Modul 1 var skrevet som en øvelse i et eget øvingsprosjekt med et eget øvingsrepo: deltakeren skulle hente oppsettet
uten tabelltypen bronze og lage bronze selv. Øvelsen kunne ikke gjennomføres (natttesten 23.–24.11):
- `.startpunkter/start-M1.startpunkt` finnes ikke, så `rm -rf specly && unzip -q .startpunkter/start-M1.startpunkt`
  slettet `specly/` og feilet.
- Et tomt prosjekt leser oppsettet inn av seg selv når det kobles til repoet (modul 0). «Se i Admin før du henter» og
  «Hent inn N i Specly» i det gamle steg 2 passet derfor ikke.

Modulen er derfor skrevet om til «se og forstå» i deltakerens eget prosjekt fra modul 0. Den eneste øvelsen er
testtabellen `brz__test__vare` i steg 3, som ble gjort og slettet i natttesten. Den gamle øvelsen ligger i Git-historien
(`moduler/M1.md` før denne endringen).

Skal øvelsen tilbake, må dette lages først:

`.startpunkter/start-M1.startpunkt` (zip, som de andre): `specly/` med hele `Config/`, `.specly.json`, `.specly/`,
`AGENTS.md` og `README.md`, men:
- ingen `Tables/`
- `Config/table_types.json` uten oppføringen `bronze`

`tools/startpunkter.py` og `tools/kursmoduler.py` trenger et tilfelle for modul 1. `./kurs til M1` og `notebooks/kurs_til`
skal ikke røre Databricks for modul 1 (modulen genererer og kjører ingenting). Nettlesersporet trenger en vei til
øvingsrepoet som ikke er «kursholderen gir deg et». Og noen må klikke gjennom øvelsen i et tomt prosjekt: om bronze
kan lages for hånd når resten av oppsettet er lest inn, og hva eksporten skriver.

### Ikke klikket i modul 1

- Steg 3, «Les mer: slik lager en admin en tabelltype fra bunnen»: «Opprett tabelltype», «Legg til kolonne» på fanen
  «Kolonnemaler» og å ta haken av felt på fanen «Metadatafelt» er sett på skjermen, men ikke trykket.
- Steg 3: hvor «Slett tabell» ligger på tabellsiden, står ikke i modulen. Testen slettet tabellen (dialogen «Er du
  sikker?» → «Slett tabell»), men noterte ikke hvor valget ligger.
- Steg 8, svaret: hva en prosjektmal tar med og ikke, er lest i Specly sin kode
  (`packages/server-core/src/services/configTemplateService.ts`, `readBranchConfig` og `buildConfigEntities`), ikke
  prøvd. Organisasjonen hadde ingen maler 23.11.
- Steg 8, «Les mer: slik lager en organisasjonsadmin malen»: «Ny mal fra prosjekt», «Kildeprosjekt» og «Opprett mal»
  er sett. Navn, beskrivelse og «Sett som standard» er ikke sett, og ingen mal er laget.
- Feltet «Mal» i dialogen «Opprett prosjekt» (modul 0, steg 3) er ikke sett. Det vises bare når organisasjonen har
  maler.

### Prosjektmal: ikke brukt

Prøvd 23.11 (prosjektet «Toppfart test»): et tomt prosjekt som kobles til et repo laget fra malrepoet, leser inn hele
`specly/Config` av seg selv, unntatt ODCS-innstillingene. Dem setter deltakeren i modul 0 steg 5. Kurset trenger derfor
ingen prosjektmal.

Vil en kursholder likevel lage en mal (for mange deltakere): lag den fra et ferdig koblet prosjekt og kall den
«Toppfart template». Lest i Specly sin kode tar malen bare med en del av oppsettet og gir alt nye uuid-er (svaret på steg
8), så deltakerne må fortsatt koble til repoet og sette ODCS-innstillingene. Det er ikke prøvd.

## Modul 8: hvor fasit kommer fra

Løsningen til modul 8 er også beskrivelsen av fasit/M8: endringene fra start/M8, som kontraktene og prosjektoppsettet
skal se ut etterpå. Verdiene står ett sted: i kontraktene og `specly/Config/table_types.json` i `specly/` (den fulle
modellen). `tools/startpunkter.py` tar dem bort i startpunktene før modul 8, og `tester/test_forhandssjekk.py` (i
utviklingsrepoet) viser at fasit går gjennom forhåndssjekken. Hvordan malene og startpunktene gjør det: «Modul 8:
slik er taggene bygget» over, og `docs/design.md` 5.6.
