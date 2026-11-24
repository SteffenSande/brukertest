# Slik setter du et startpunkt

Hver modul fra 2 til 11 har et startpunkt: modellen slik den er når modulen begynner. Du trenger det bare når du ikke
fortsetter rett fra modulen før, eller vil begynne en modul på nytt. Modul 0 og 1 har ikke noe startpunkt.

**Dette skjer:** modellen i `specly/` skrives over med startpunktet, koden genereres, og pipelinen bygger alle
tabellene på nytt. Tabeller i skjemaet ditt som ikke hører til startpunktet, slettes. Du får se hva som går tapt, og
må bekrefte før noe skrives over eller slettes. Det du har committet, finner du igjen i Git.

**Har du laget tabeller selv i Specly-prosjektet ditt, si fra til kursholderen før du setter et startpunkt.**
Startpunktet har de samme tabellnavnene som dine, men er ikke de samme tabellene. Specly stopper da «Hent inn» med
meldingen «Det finnes allerede en tabell med navnet …», og du får ikke valgt noe. Mangler du bare tabeller fra modulen
du er i, bruker du `fyll` i stedet (se [Om `fyll`](#om-fyll)): den legger til det som mangler og rører ikke det du har.

Eksemplene bruker `M4`. Bytt det med modulen du skal til.

## Terminalsporet

1. `./kurs til M4`
2. `git add specly && git commit -m "Til M4" && git push`
3. I Specly: «Import og eksport» → «Importer fra Git». Se over listen under «Fra Git» («KOMMER INN · N»), og trykk
   knappen «Hent inn til …». Den slutter med koden for den siste commiten i Git, for eksempel «Hent inn til ea94b55».
   Åpner den en side med konflikter, se [Konfliktsiden ved «Hent inn»](#konfliktsiden) under.

   Har Git nye commits, står linjen «N endringer på main» øverst i menyen under «Import og eksport», og valgene
   under flytter seg ned. Se at du treffer «Importer fra Git», ikke «Importer fra Fabric».

## Nettlesersporet

1. Åpne notebooken `notebooks/kurs_til`. Har du aldri kjørt den (eller nettopp gjort «Pull»), har den ingen felt
   ennå («No parameters»). Kjør da bare den første kodecellen, den som begynner med kommentaren «Feltene»: hold
   pekeren over cellen og trykk ▶ øverst til venstre i den. Cellen lager feltene i sidepanelet «Parameters» (knappen
   «Show parameters») og endrer ingenting.
2. Velg «Til» = `start/M4`. Listen viser ikke alle valgene: rull ned i listen for `fasit/…`, klikk på valget, og se
   at feltet viser det du valgte. Bruker du et annet skjema enn `toppfart`, skriver du det i «Skjema». La «Bekreft
   (skriv over og slett)» stå på `nei`.
3. Trykk «Run all». Nå skjer én av to ting:
   - **Noe går tapt** (filer i modellen som er ulike startpunktet, eller tabeller som slettes): notebooken viser
     listen og stopper før noe er endret. Meldingen begynner med «Stoppet: …». Les listen, sett «Bekreft» til `ja`,
     og trykk «Run all» igjen.
   - **Ingenting går tapt:** det er ingenting å bekrefte, og notebooken kjører rett gjennom med «Bekreft» = `nei`.
     Modellen byttes, koden genereres og pipelinen bygger tabellene på nytt. Det tar noen minutter.
4. Notebooken er ferdig når den siste cellen skriver «Ferdig: modellen og Databricks står på start/M4.» Den setter
   selv «Bekreft» tilbake til `nei`, så neste kjøring viser listen igjen. Se at feltet står på `nei`.
5. Commit og push i Git-mappen i Databricks: trykk på branchnavnet, skriv en melding og trykk «Commit & Push».
6. I Specly: «Import og eksport» → «Importer fra Git», og knappen «Hent inn til …», som i punkt 3 i
   terminalsporet.

Trykker du «Run all» uten å kjøre cellen «Feltene» først, går notebooken med standardverdiene: «Til» = `start/M4`,
skjema `toppfart` og «Bekreft» = `nei`. Går noe tapt, stopper den. Går ingenting tapt, kjører den rett gjennom til
`start/M4`.

Når notebooken stopper, står utskriftene fra forrige kjøring igjen i cellene under («Skipped — showing output from
previous execution»). Det som gjelder, er meldingen «Stoppet: …».

Feltene i notebooken blir borte igjen etter hver «Pull». Se [Notebookene etter «Pull»](#notebookene-etter-pull).

## Etter «Hent inn»

<a id="regeldialogen"></a>Når «Hent inn» går rent, kommer en melding nederst til høyre, for eksempel «Main står nå
på» og koden fra Git, eller «Endringene fra Git er hentet», og «Reglene sjekkes når du går til Utvikling». Siden «Importer fra Git» sier «I synk: Specly og
main er like».

Specly sjekker så hva reglene ville endret i tabellene som kom inn. Specly kjører ikke reglene av seg selv. Ville en
regel endret noe, kommer dialogen **«Regler for det som kom inn fra Git»**. Den har én rad med hakeboks per regel
(«Flaggregler», «Kolonnesortering», «Relasjonsregler», «Begrepsregler»), og sier «Ingen endringer» eller hva regelen
ville gjort, for eksempel «2 nye relasjoner». Nederst står knappene «Ikke kjør reglene» og «Kjør valgte». «Kjør
valgte» er grå til du har haket av noe. Sjekken finnes fordi en endring i Git ikke har gått gjennom Specly: kanskje er
en kolonne lagt til nederst for hånd, eller en `fb__` mangler FK-flagget.

**Anbefaling:** Kommer dialogen, se hvilke tabeller det gjelder. Sier modulen hva du skal velge, gjør det. Ellers er
«Ikke kjør reglene» alltid trygt: ingenting endres, og du kan kjøre reglene senere med «Bruk regler» på tabellen.
Startpunktene i kurset følger reglene, så for dem skal dialogen ikke foreslå noe du må ta stilling til.

Reglene selv er forklart i [modul 2](M2.md), «Regler i prosjektet».

## Konfliktsiden ved «Hent inn»

<a id="konfliktsiden"></a>Når det bare er Git som har endret seg, tar «Hent inn» endringene inn uten spørsmål. Det
gjelder også når du har endret noe annet i Specly i mellomtiden. Etter `fyll` skal du ikke se denne siden.

**En ekte konflikt** er at det samme feltet er endret på begge sider siden forrige synk. Eksempel: du skriver en
beskrivelse på `slv__salgslinje` i Specly, og noen har skrevet en annen beskrivelse på samme tabell i Git.

- Siden «Importer fra Git» varsler før du trykker. Over «KOMMER INN» står «MÅ VELGES · 1», tabellen er merket «VELG»,
  og teksten sier «Beskrivelse på slv__salgslinje er endret i Specly, og Git har en annen versjon.»
- «Hent inn til …» åpner da siden **«Hent endringer fra Git»**, med «1 konflikt» og teksten «Velg en side for hver
  konflikt før du fortsetter.» Konflikten har navnet på tabellen eller kolonnen som overskrift og feltet under
  (`description`), og viser tre verdier: «Før» (verdien ved forrige synk), «min» (det Specly har) og «Git».
- Under konfliktene står «Endringer på bare én side». De tas inn eller beholdes uten at du velger noe.

**Gjør:**
1. Velg side på hver konflikt: «Behold min» eller «Ta Git sin». «Behold alle mine» og «Ta alle fra Git» øverst til
   høyre velger samme side for alle. Den siden du ikke velger, går tapt for det feltet.
2. Trykk «Hent fra Git» i linjen nederst på siden. Knappen er grå så lenge noen konflikter ikke er valgt («N
   konflikter er ikke valgt»).
3. Du kommer tilbake til Git-siden, og dialogen «Regler for det som kom inn fra Git» (se over) kan komme.

Står det under «min» en verdi du ikke har skrevet selv i Specly, er konflikten ikke din. Velg «Ta Git sin». Unntaket
er begrepene fra modul 9, se under.

**To tilfeller der siden kan komme uten at du har endret det samme i Git:**

- **Du har satt et startpunkt som tar bort tabeller du har arbeidet med i Specly.** Da kan det stå en konflikt på
  `metadataTextValues` på en kolonne, med «Før: —», «min: {"beregning": ""}» og «Git: fjernet». Startpunktet skal
  erstatte det du hadde: velg «Ta Git sin».
- **Du har gjort modul 9 (koblet kolonner til begreper), og henter så inn noe annet.** Da kunne det tidligere komme
  konflikter på `replacedText` og `previousValues` under begrepene, med «—» på Git-siden. Det er teksten kolonnen
  hadde før begrepet overskrev den, og den finnes bare i Specly: velg «Behold min» på dem. Velger du «Ta Git sin»,
  er kolonnen fortsatt koblet, men den gamle teksten kommer ikke tilbake hvis du senere kobler den fra.

## Notebookene etter «Pull»

<a id="notebookene-etter-pull"></a>Gjelder nettlesersporet, i alle modulene.

- **Feltene er borte.** Etter hver «Pull» i Git-mappen (og «Pull anyway») står notebookene uten felt («No
  parameters»), også de du har kjørt før. Trykk «Run all» én gang, så kommer feltene tilbake i sidepanelet
  «Parameters» (knappen «Show parameters»). Den første kjøringen går med standardverdiene. `kurs_sjekk` og `kurs_fyll` har
  standarden «Velg modul»: de stopper uten å sjekke eller endre noe, og ber deg velge modul. Velg modulen din i feltet
  «Modul», vent til «Run all» er tilbake, og trykk «Run all» igjen.
  For `kurs_sjekk`: se at den siste cellen sier «Fasittest (modul 2-N)» med din modul som N.
- **Vil du sette feltene før første kjøring** (et annet skjema enn `toppfart`, eller en annen modul)? Kjør bare den
  første kodecellen, den som begynner med kommentaren «Feltene»: hold pekeren over cellen og trykk ▶ øverst til
  venstre i den. Den lager feltene og gjør ikke noe annet. Sett feltene, og trykk så «Run all». Standardskjemaet
  `toppfart` er riktig for de fleste. Bruker du et annet, må du sette det slik i hver notebook etter hver «Pull».
- **«Run all» rett etter at du har endret et felt, gjør ingenting.** Når du endrer et felt, kjører Databricks cellen
  som leser feltene på nytt av seg selv. Mens den går, står det «Interrupt» der «Run all» pleier å stå (noen
  sekunder, i `kurs_sjekk` opptil ti). Trykker du «Run all» for tidlig, blir den cellen avbrutt («Cancelled»), og
  ingenting annet kjører. Utskriftene fra forrige kjøring står igjen, så det kan se ut som notebooken har gått. Vent
  til «Run all» er tilbake, og trykk da.
- **Listene i feltene «Modul» og «Til» er lengre enn de ser ut.** «Modul» viser `M2` til `M8`. `M9`, `M10` og `M11`
  ligger under kanten, og i «Til» ligger `fasit/…` under kanten. Rull ned i listen og klikk på valget. Piltastene
  treffer ikke alltid riktig valg, så se at feltet viser det du valgte. Å skrive `M11` i feltet filtrerer ikke listen.
- **Resultatet står nederst.** Utskriften i en celle står i en boks du må rulle i når den er lang. Notebookene
  skriver derfor resultatet i den siste cellen: `kurs_sjekk` linjene om kontraktene (fra modul 9 også begrepene, fra modul 10 dataproduktet),
  tallene og taggene,
  `kurs_til` «Ferdig: modellen og Databricks står på …», og `kurs_generer_kjor` «Ferdig: N tabeller i …».
- **Gammel utskrift blir stående.** Stopper en notebook tidlig (`kurs_fyll` og `kurs_sjekk` på «Velg modul», `kurs_til` på listen
  over det som går tapt), viser cellene under utskriften fra forrige kjøring, merket «Skipped — showing output from
  previous execution». Det som gjelder, er meldingen notebooken stoppet med («Notebook exited: …»).
- **«Attached cluster is terminated».** Har notebooken stått en stund, kan «Run all» gi en dialog som sier at
  notebooken er koblet til en «cluster which has terminated», med knappen «Select resource». Trykk «Cancel». Trykk
  på «Serverless» i verktøylinjen øverst i notebooken, velg «Serverless», og trykk «Run all» igjen. (Dialogen tilbyr
  et «SQL Warehouse». Det kan ikke kjøre disse notebookene.)
- Banneret «This file is part of a bundle. Switch to associated bundle.» øverst i notebooken kan du se bort fra.

## Om `fyll`

<a id="om-fyll"></a>Noen tabeller lager du ikke selv, fordi de er samme håndverk som du nettopp har gjort. Dem legger
kurset inn for deg: `./kurs fyll M4` i terminalsporet, eller notebooken `notebooks/kurs_fyll` med «Modul» = `M4` i
nettlesersporet. `fyll` finnes for modul 3, 4, 5, 6, 7 og 11.

- **Dette skjer:** kontraktfilene for tabellene kopieres fra fasit for modulen inn i `specly/`. Tabeller du alt har,
  blir stående urørt. Ingenting annet endres: `fyll` committer ikke, og rører verken Specly eller Databricks.
- **Etterpå** committer og pusher du (`git add specly && git commit -m "fyll M4" && git push`, eller «Commit & Push» i
  Git-mappen i Databricks), og henter inn i Specly: «Import og eksport» → «Importer fra Git» → «Hent inn til …».
  Modulen sier når du gjør det, og hva du eksporterer først.
- **Hvorfor det går an:** kurset har bestemt forretningsbehovet og har en fasit. I virkeligheten finnes det ingen
  fasit å fylle fra. Modellen må lages ut fra hva forretningen trenger, og det er det kurset øver på.

## Sluttpunktet for en modul

Vil du se modellen slik den er når en modul er ferdig, bruker du `fasit/M4` i stedet: `./kurs til fasit/M4`, eller
«Til» = `fasit/M4` i notebooken. Alt annet er likt.
