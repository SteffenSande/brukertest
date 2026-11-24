# Kjente feil og friksjon i Specly

*Sist gjennomgått 24.11.2026, etter natttesten 23.-24.11 der modul 0-11 ble gjennomført på test.specly.no i et
prosjekt laget fra kursmalen. Hver feil og hver friksjonslinje har nå en status.*

**Hvor listen kommer fra.** Feil 1-6 og friksjon 7-17 er fra det forrige demoprosjektet (`~/specly-demo-plattform`,
17.11 og 21.11). Resten ble sett i natttesten. Linjene merket «Natttesten» under hver feil er det som ble sett da,
modul for modul.

**Hva som ble rettet i natt.** Funnene ble meldt i fem Devly-chatter på `SteffenSande/specly`. Oppgavene fra dem står
alle i «done», og pull requestene er slått sammen i Specly. Sluttoppsummeringen fra natten sier 20 oppgaver. Oversikten
over chattene lister 19 (3 + 3 + 3 + 5 + 5), og det er dem denne filen viser til:

| Chat (startet) | Oppgaver | Pull requests i Specly | Her i listen |
|---|---|---|---|
| `cmwtui388000d01hzm7lppfnn` (23.11 kl. 23.36) | tabell-deltaer til alle sync-poder, kortet «Standardkolonner», rekkefølgen i JSON-registerfilene | #3264, #3262, #3263 | feil 22, 23, 24 |
| `cmwtw5ehh000r01hzfw1rzs7l` (24.11 kl. 00.20) | falske konflikter (normaliserte verdier), konfliktsiden («velg alle», fast handlingslinje), eksport av slettet kolonne med relasjon | #3269, #3265, #3267 | feil 7, 8 |
| `cmwtxlwdi000w01hzpprof4wf` (24.11 kl. 01.05) | dobbel oppstrøm og diagrammedlemskap, Enter i tabellfelt, `projectId` i `.specly.json` | #3272, #3271, #3273 | feil 9, 11, 10 |
| `cmwtz9qen001101hzxjltgbzu` (24.11 kl. 01.50) | ingen konflikt når noe laget i Specly endres i Git, melding når PR-rettigheten mangler, kladd og sammenligning for forslag, «Opprett ny tabell», småting | #3279, #3276, #3278, #3274, #3277 | feil 13, 14, 15, friksjon 23 |
| `cmwu0qsum001801hz9neg0ehr` (24.11 kl. 02.30) | én begrepsregel per innhold, `replacedText`/`previousValues` ut av sammenligningen, «Bruk regler» viser tekstene, småting, dataproduktmedlem fjernet i Git | #3284, #3285, #3280, #3282 og én uten nummer i notatene (startet på nytt kl. 07.20) | feil 16, 18, friksjon 28, feil 17 |

For de to siste chattene står oppgavene og pull requestene i samme rekkefølge i nattnotatene, men hvilken PR som
hører til hvilken oppgave, er ikke kontrollert. Hva de to småting-oppgavene (#3277 og #3282) dekker, står ikke i
notatene.

**Statusene.** Hver feil har én av disse:

- **Rettet og sett virke på test 24.11:** rettelsen er slått sammen, og natttesten så på skjermen at feilen var borte
  etterpå.
- **Rettet i Specly 24.11, ikke kontrollert på skjermen:** oppgaven står i «done» og PR-en er slått sammen, men ingen
  har sett på test at feilen er borte. Må klikkes før kurset.
- **Åpen:** ikke meldt i natt, eller ikke rettet.
- **Ikke gjengitt 24.11:** brukt om eldre feil som natttesten prøvde uten å få fram. De var ikke blant nattens
  oppgaver.

| Status | Feil | Friksjon |
|---|---|---|
| Rettet og sett virke på test 24.11 | 7, 9, 10 | 9 og 10 (rettet før natttesten) |
| Rettet i Specly 24.11, ikke kontrollert på skjermen | 8, 11, 13, 14, 15, 16, 17, 18, 22, 23, 24 | 23, 28 |
| Åpen | 3, 4, 5, 6, 12, 19, 20, 21 | resten (29 linjer) |
| Ikke gjengitt 24.11 | 1, 2 | |

**Merk om feil 16 og 18.** Natttesten av modul 11 så kl. 02.38 at reglene ikke ble doble og at konfliktene på
`replacedText` og `previousValues` ikke kom. Oppgavene for akkurat de to feilene ble startet kl. 02.40, altså etter
det. Det som ble sett, kan derfor skyldes en av de tidligere rettelsene samme natt. Ingen har sett på skjermen etter
at de to pull requestene ble slått sammen, og derfor står de som «ikke kontrollert».

**Ikke Specly-feil, men stopper et steg:**
- «Send inn forslag» i modul 8 steg 6 åpner en pull request fra Specly. Appen på test manglet 24.11 «Pull
  requests: Read and write», og da får deltakeren en melding med lenke til å åpne den selv.
- «Importer fra Databricks» krever et personlig Databricks-token. Natttesten skrev ikke inn tokens, så alt etter
  «Koble til Databricks» i modul 2 er ikke klikket. CSV-omveien virket.

Merket: **[V]** sett og gjengitt, **[A]** antatt eller sett én gang.

## Feil som rammer kurset

### 1. «Hent inn» på main feiler når en ny kolonne og lineage til den kommer i samme push [V, 17.11]
- **Status 24.11:** **ikke gjengitt.** Prøvd nøyaktig i natttesten av modul 5 og 6, og «Hent inn» tok begge kolonnene.
  Ikke blant nattens oppgaver: trolig rettet før natttesten [A]. Advarslene er ute av modul 5, 6 og 7.
- **Gjengi:** På en branch: legg kolonnen `website` til i `raw__crm__account`, og en bronze-kolonne med
  oppstrøm `raw__crm__account.website`. Eksporter. Spol Git main fram til branchen. Åpne «Eksporter til Git» på
  Specly main.
- **Forventet:** «Fra Git» lister endringene, «Hent inn» tar dem.
- **Faktisk:** «Fra Git 0». Banneret sier at kilden `raw__crm__account.website` ikke finnes i Specly. Feilen
  pekes på feil tabell (`gold__f__henvendelse`, som ikke har noe med `website` å gjøre). Kunden står fast uten å
  endre Git.
- **Omvei:** to commits (ta lineage ut, hent inn, legg den tilbake, hent inn).
- **Notat 22.11:** `f9241b6a6` («Hent inn alt» tar nye tabeller som navngir nye kolonner i levende tabeller) kan
  ha rettet deler av dette. Den beskriver en ny *tabell* som leser en ny kolonne. Feilen over gjaldt en ny
  kolonne i en *eksisterende* tabell.
- **Rammer kurset:** modul 6 (endring via Git).
- **Natttesten:** traff ikke i modul 3 og 4. `./kurs fyll` legger bare til nye tabeller, og de kom inn med oppstrøm
  uten banner. Selve tilfellet (ny kolonne i en eksisterende tabell) er ikke prøvd. Det som stoppet «Hent inn» i
  modul 3 og 4, er feil 7.
- **Natttesten, modul 5 og 6:** lot seg ikke gjengi. Prøvd nøyaktig: én commit med en ny kolonne `test_kolonne` i
  `raw__nettora__ordrelinje` (uten id) og en ny kolonne i `brz__nettora__ordrelinje` med oppstrøm til den. «Fra Git»
  viste begge under «KOMMER INN · 2», uten banner, og «Hent inn» tok dem. `git revert` etterpå ble også hentet inn
  rent (begge merket «SLETTET»). Advarslene om feilen er tatt ut av modul 5 og 6.
- **Natttesten, modul 7 og 8:** traff ikke. `fb__slv__kunde` med relasjon i `slv__salgslinje` og `fk__gld__d__kunde`
  med relasjon i `gld__f__salg` gikk gjennom i én eksport. Feilboksen er tatt ut av modul 7.

### 2. Eksporten fjerner `fagekspert` fra begrepsfilene [V, 21.11]
- **Status 24.11:** **ikke gjengitt, og rammer ikke kurset.** Kursprosjektet har ikke feltet. Prøvd med et midlertidig
  felt i natttesten av modul 9 og 10, uten å få fram feilen. Ikke blant nattens oppgaver.
- **Gjengi:** Koble en kolonne til et begrep som har en fagekspert, og eksporter.
- **Forventet:** Begrepsfilen beholder `fagekspert`.
- **Faktisk:** Feltet fjernes, også fra begreper du bare har koblet en kolonne til. Begrepssiden viser
  personen som «ikke i personregisteret», selv om personen står i personkatalogen.
- **Notat 22.11:** ingen commit funnet som nevner dette. Merk at demoprosjektet fjernet feltet `fagekspert` fra
  oppsettet 22.11, så feilen kan skyldes at feltdefinisjonen manglet.
- **Natttesten, modul 7 og 8:** ikke prøvd (begreper kommer i modul 9). En lignende feil for tabellfeltet Eier er
  rettet: Eier eksporteres nå som `team.name`.
- **Natttesten, modul 9 og 10:** ikke gjengitt. Kursprosjektet har ikke noe felt `fagekspert`: begrepssiden har
  Forretningsbeskrivelse, Utviklernotat, Nedstrømsnavn, Datatype og Klassifisering, «Admin» → «Metadatafelt» → fanen
  «Forretningsbegrep» sier «Ingen felt er koblet til ennå», og de fire begrepsfilene fra modul 9 har bare `columns`,
  `dataType`, `name`, `rules` og `uuid`. Prøvd med et midlertidig felt: «Nytt felt» `Fagekspert` (nivå
  Forretningsbegrep, felttype Person), en person uten konto i «Personer», valgt på et begrep. To eksporter, den andre
  etter at en kolonne var koblet til for hånd: `metadata.fagekspert` sto i filen begge ganger, og teksten «ikke i
  personregisteret» kom aldri. Ikke prøvd: en bruker med konto som fagekspert, og «Hent inn» av en fil med feltet.
  Feltet og personen er slettet igjen.
- **Rammer kurset:** ikke i dag. Prosjektoppsettet har ikke feltet.

### 3. «Opprett relasjon» foreslår feil kolonnepar [V, 21.11]
- **Status 24.11:** **åpen.** Delvis rettet før natttesten: forslagene var riktige fra `fb__` til sølv og fra faktaen
  til dimensjonene. Mellom to bronze-tabeller foreslår dialogen fortsatt feil par (sett i modul 4). Ikke blant nattens
  oppgaver.
- **Gjengi:** I et diagram med en fakta og flere dimensjoner: tegn relasjonen til kundedimensjonen først, så
  til kundegruppedimensjonen.
- **Forventet:** forslaget `fk__kundegruppe` → `pk__gold__d__kundegruppe`.
- **Faktisk:** forslaget `fk__kunde` → `pk__gold__d__kundegruppe`.
- **Notat 22.11:** `f216d7699` («Opprett relasjon: direction and column pairs guessed …») og `799a2275b` endret
  dialogen.
- **Rammer kurset:** modul 4 og 5.
- **Natttesten:** fra en `fb__` til en sølvtabell foreslår dialogen riktig par og kardinalitet (`fb__` → `bk__`,
  `0..N` og `0..1`). Mellom to bronze-tabeller foreslår den fortsatt feil (`bk__` → `pk__`, modul 4 steg 4).
- **Natttesten, modul 5 og 6:** fra faktaen til tre dimensjoner etter hverandre (produkt, butikk, dato) var alle
  forslagene riktige: `fk__` → `pk__`, `0..N` og `1`.

### 4. «Sorter kolonner» sorterer med en gang og kan ikke angres [V, 21.11]
- **Status 24.11:** **åpen.** Delvis rettet før natttesten: valget står nederst i menyen og spør først. Det kan
  fortsatt ikke angres, og BK-kolonnene sorteres alfabetisk. Kurset ber nå om sortering, så fasit og deltaker får
  samme rekkefølge. Ikke blant nattens oppgaver.
- **Gjengi:** Tabellsiden → «Bruk regler» → «Sorter kolonner».
- **Faktisk:** Kolonnene sorteres alfabetisk uten spørsmål, og Ctrl/Cmd+Z angrer ikke. Valget står øverst i
  samme meny som «Finn forretningsbegrep», så det er lett å treffe. I en fakta der rekkefølgen på BK-kolonnene
  betyr noe, ble modellen feil. Eneste vei tilbake var «Forkast endringer» på Git-siden etter eksport.
- **Forslag:** spør før sortering, eller la det kunne angres. Legg valget lenger fra «Finn forretningsbegrep».
- **Natttesten:** delvis rettet. Valget står nå nederst i menyen, bak en skillestrek. Det åpner dialogen «Sortere
  kolonnene?» med «Avbryt» og «Sorter», og dialogen sier «Dette kan ikke angres med Ctrl+Z.» Det kan fortsatt ikke
  angres. Sorteringen stiller BK-kolonnene alfabetisk, og koden regner nøkkelen i den rekkefølgen. Fasit er sortert.
- **Natttesten, modul 5 og 6:** samme dialog i gull. `gld__f__salg` ble etter «Sorter» lik fasit (`pk__`, de tre
  `fk__`, BK-kolonnene `butikknummer`, `linjenummer`, `salgsnummer`, resten alfabetisk, `sys__` sist). Modul 5 ber nå
  om sortering, og «Trykk aldri» er strøket.
- **Rammer kurset:** modul 5 og 9.

### 5. `businessName` skrives ikke for begrepskoblinger med unntak laget i grensesnittet [V, 17.11]
- **Status 24.11:** **åpen, rammer ikke kurset.** Ikke prøvd som feil i natttesten: i kursprosjektet er `businessName`
  nedstrømsnavnet. Ikke blant nattens oppgaver.
- **Gjengi:** Lag kolonner med egen beskrivelse. «Bruk regler» → «Finn forretningsbegrep» → «Koble valgte»
  (kolonnene får «overstyrt»). Eksporter.
- **Forventet:** `businessName: <begrep>` på kolonnen, som i kontrakter skrevet i Git.
- **Faktisk:** Begrepsfilen får koblingen, men kontrakten får ingen `businessName`.
- **Merk:** Demoprosjektet skriver nå nedstrømsnavnet til `businessName` (`columnBusinessNameSource:
  downstreamName`). Hva som skal skje når begge finnes, bør avklares.
- **Natttesten, modul 9 og 10:** ikke relevant i kursprosjektet. Der er `businessName` nedstrømsnavnet, og
  kontraktene fikk bare `description` fra begrepene.
- **Rammer kurset:** ikke i dag.

### 6. Raden «Nytt filformat» og banneret om eldre format [A, 21.11]
- **Status 24.11:** **åpen (uavklart).** Banneret ble ikke sett ved første eksport i natttesten. Raden kom i modul 6
  etter «Skriv alle kontrakter på nytt…», med filer ingen hadde endret. Ikke blant nattens oppgaver.
- **Faktisk:** Lokalt sto det fra start en rad «Nytt filformat: … filer skrives på nytt» og et banner. Telleren
  i branchbanneret viste «↑ 0+3». Mistanken er at ODCS-innstillingene ikke ble lest fra `Config/` lokalt.
- **Rammer kurset:** modul 2 og utover (forvirrende ved første eksport).
- **Natttesten, modul 5 og 6:** etter «Skriv alle kontrakter på nytt…» → «Finn kontrakter som er ulike» kom banneret
  og raden «Nytt filformat: 6 filer skrives på nytt». Listen hadde `metadata_field_definitions.json` og alle fire
  diagramfilene, som ingen hadde endret, i tillegg til kontrakten uten id. Trolig fordi Specly ble oppdatert i løpet
  av natten. Modul 6 steg 2 bruker nå denne veien, og sier at flere filer kan stå i listen.

### 7. «Hent inn» etter en ren Git-commit åpner en konfliktside med bare falske konflikter [V, 24.11]
- **Status 24.11:** **rettet og sett virke på test 24.11.** PR #3269 (normaliserte verdier sammenlignes) og #3265
  («Behold alle mine», «Ta alle fra Git» og «Hent fra Git» i en fast bunnlinje). Sett: knappene (modul 6), de tre
  siste «Hent inn» i modul 6 uten konfliktside, og to «Hent inn» i modul 11 med 0 konflikter. Varianten med tomt
  `radfilter` (1 konflikt i modul 7) ble meldt i chatten kl. 01.50. **Ikke sett:** gjengivelsen under gjentatt i et
  nytt prosjekt (`fyll M3` etter tabeller laget for hånd), og «Hent inn» etter `./kurs til`. Derfor står «kan
  komme»-blokkene i kurset til det er prøvd (`docs/kursholder.md`).
- **Gjengi:** Lag tabeller i grensesnittet og eksporter. Legg nye kontraktfiler rett i Git (`./kurs fyll M3`), uten
  å røre noe annet. «Importer fra Git» viser «Mine endringer 0» og «KOMMER INN · 2». Trykk «Hent inn til <kode>».
- **Forventet:** tabellene hentes inn uten spørsmål.
- **Faktisk:** siden «Hent endringer fra Git» med 39 konflikter (modul 3) og 19 (modul 4), på `columnStatusUuid`,
  `tableTypeMetadata` og `metadataValues` for tabellene som er laget i grensesnittet. Ingen «velg alle», og «Hent
  fra Git» står nederst på en lang side.
- **Omvei:** velg en side på alle («Ta Git sin» og «Behold min» virket begge), og trykk «Hent fra Git».
- **Rammer kurset:** ikke lenger etter `fyll` (se prøven på dagtid 24.11 under). `moduler/start.md` forklarer siden
  for ekte konflikter og for et startpunkt som tar bort tabeller.
- **Natttesten, modul 5 og 6:** 49 konflikter etter `fyll M5` (kl. 00:28): 42 på `columnStatusUuid`, 3 på
  `tableTypeMetadata` og 4 på `relations` (`fromColumnUuids` og `toColumnUuids`, «min» `—` mot «Git» `[]`), med en
  uuid som overskrift. `slv__salgslinje` fra modul 4 kom med igjen. Etter `fyll M6` (kl. 00:43) var siden endret: 6
  konflikter, alle på `relations`, nye knapper «Behold alle mine» og «Ta alle fra Git», og «Hent fra Git» i en fast
  bunnlinje. «Behold alle mine» ble trykket og virket. «Ta alle fra Git» er ikke trykket. De tre neste «Hent inn» ga
  ingen konfliktside. Etter «Hent fra Git» i modul 5 kom dialogen «Regler for det som kom inn fra Git» oppå siden
  «Skjema-valideringer».
- **Natttesten, modul 7 og 8:** 1 konflikt etter `fyll M7`: `slv__salgslinje`, `tableTypeMetadata`, «min» har
  `"radfilter":""`, «Git» har ikke nøkkelen, «Før» er «—». Under «Endringer på bare én side» sto `slv__butikk` med
  `{"radfilter":"AKTTYPE = 'B'"}` → `{"union_av":"","radfilter":"AKTTYPE = 'B'"}`. Trolig normaliseres ikke tomme
  verdier i `tableTypeMetadata` likt på de to sidene. «Ta alle fra Git» ble trykket og virket. Kurset anbefaler nå
  den overalt (se feil 13).
- **Natttesten, modul 11:** siden kom ikke. To «Hent inn» på rad (en ny raw-kontrakt skrevet i Git, og `fyll M11`)
  ga 0 konflikter, etter flere rettelser i Specly samme natt.
- **Prøvd på nytt 24.11 på dagtid: ikke gjengitt etter `fyll`.** `fyll M3`, `M4`, `M5`, `M6` og `M7` ble kjørt på
  nytt mot de samme kontraktene som i natt, og «Hent inn til <kode>» ga 0 konflikter alle fem gangene (39, 19, 49, 6
  og 1 i natt). I modul 3 var tabellene ved siden av laget i Specly, som i natt. I modul 4 til 7 var sølv og gull
  kommet inn fra Git. Omvei-blokkene i modul 3 til 8 er tatt ut (`docs/kursholder.md`).
- **To falske konflikter sto igjen i samme prøve, utenfor `fyll`:** (1) Da Git slettet 24 tabeller (modellen satt
  tilbake til før `fyll M3`): 1 konflikt på `slv__butikk.butikknavn`, `metadataTextValues`, «Før: —», «min:
  {"beregning": ""}», «Git: fjernet». Samme mønster som `"radfilter":""` i modul 7: en tom verdi i Specly som ikke
  står i Git. Å tømme Radfilter på en ny tabell og slette den i Git ga ingen konflikt, så dette er ikke gjengitt på
  nye data. (2) Etter «Gjør lik Git…»: en beskrivelse skrevet i Git på `brz__varius__vare` ga 1 konflikt på
  `description` med «Før: —» og «min: <en tekst som var hentet inn fra Git to synk tidligere, og fjernet igjen fra
  Git>». Tabellsiden viste tom beskrivelse, og Git-siden «Mine endringer 0». Under «Endringer på bare én side» sto
  `order`-endringer på «min» som Git-siden heller ikke viste. Konfliktsiden regner trolig fra et eldre utgangspunkt
  enn Git-siden etter «Gjør lik Git…» [A].

### 8. Eksport feiler når en eksportert kolonne med relasjon slettes [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3267.
- **Gjengi:** Legg `fb__slv__leverandor` til i `slv__salgslinje` (som er i Git), «Finn relasjoner», eksporter. Slett
  kolonnen, og eksporter igjen.
- **Faktisk:** «Eksport feilet … Relasjonen slv__salgslinje.fb__slv__leverandor → slv__leverandor.bk__slv__leverandor
  finnes verken i Git-filen eller i Specly-filen».
- **Omvei:** `git revert` av commiten med kolonnen, og push.
- **Rammer kurset:** modul 4 og utover, for den som lager en `fb__` feil og sletter den.

### 9. Etter «Hent fra Git» på konfliktsiden vises hver oppstrømskolonne to ganger [V, 24.11]
- **Status 24.11:** **rettet og sett virke på test 24.11.** PR #3272. Sett: én oppstrømskolonne per kolonne i
  `slv__salgslinje` og `gld__f__salg`. **Ikke sett på nytt:** antallet i diagramlisten.
- **Gjengi:** som feil 7 (tabeller laget i grensesnittet, eksportert, så `fyll` og «Hent inn» med konfliktside, valgfri
  side, «Hent fra Git»). Åpne en tabell som er laget i grensesnittet.
- **Forventet:** én oppstrøm per kolonne i «Oppstrømskolonne».
- **Faktisk:** `gld__f__salg`: `butikknummer` viser `slv__salgslinje.butikknummer` to ganger, og slik for alle
  kolonner med oppstrøm. Samme i `gld__d__produkt` og `brz__varius__vare`. Står også etter ny sidelasting, og i
  blyanten («VALGTE KILDER (3)» der det skulle vært 2; × på den ene fjerner begge). «Mine endringer» viser 0, og
  kontrakten i Git har én linje per kilde. Diagramlisten viser dobbelt antall tabeller («Sølv 10» for 5 tabeller).
- **Natttesten, modul 9 og 10:** rettet. `slv__salgslinje` (kl. 01:57) og `gld__f__salg` (kl. 02:14, etter en ny
  «Hent inn» via konfliktsiden) viser én oppstrømskolonne per kolonne, og to der kolonnen har kilde i både kasse og
  nett. Diagramlisten er ikke sett på nytt.
- **Rammer kurset:** ikke lenger. Merknaden `OMVEI-DOBBEL-OPPSTROM` i modul 6 er tatt ut.

### 10. `specly.py fix --add-ids` stopper: `.specly.json` får aldri `projectId` [V, 24.11]
- **Status 24.11:** **rettet og sett virke på test 24.11.** PR #3273: eksporten skriver `projectId` når den mangler.
  Sett: `projectId` i filen etter eksporten i modul 9, og `fix --add-ids` skrev id-er i modul 11.
- **Gjengi:** repo fra kursmalen (`specly/.specly.json` uten `projectId`), koblet til et Specly-prosjekt. Eksporter
  flere ganger. Kjør `specly.py fix --add-ids --changed-from main` med en ny kontrakt uten id.
- **Forventet:** `projectId` er skrevet inn ved første eksport, og `fix` lager id-ene.
- **Faktisk:** «fix --add-ids: specly/.specly.json har ingen projectId, så id-ene Specly ville laget kan ikke regnes
  ut. Gjør en skriving fra Specly til branchen.» Ingen av 13 eksporter, heller ikke «Skriv nytt filformat», endret
  `.specly.json`.
- **Omvei:** commit kontrakten uten id, «Hent inn», «Skriv alle kontrakter på nytt…» → «Skriv nytt filformat».
- **Merk:** kan like gjerne være en feil i kursmalen: `tools/lag_kursrepo.py` tar `projectId` ut med vilje.
- **Natttesten, modul 9 og 10:** eksporten i modul 9 skrev `"projectId"` inn i `specly/.specly.json`. `fix
  --add-ids` er ikke prøvd på nytt.
- **Natttesten, modul 11:** rettet. `projectId` sto i `specly/.specly.json`, og `fix --add-ids --changed-from main`
  skrev ti id-er på en ny raw-kontrakt («fix skriver 1 fil: 1 kontrakter med nye id-er …»). Språk i utskriften: «1
  kontrakter».
- **Rammer kurset:** ikke lenger. Modul 6 steg 1 bruker `fix --add-ids` igjen, med forutsetningen at prosjektet har
  eksportert til repoet minst én gang. Omveien `OMVEI-PROSJEKTID` er tatt ut.

### 11. «Union av»: Enter i søkefeltet velger feil tabell, og søket blir stående usynlig [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3271 (Enter i tabellfelt). Om søket
  som ble stående usynlig, også er rettet, står ikke i notatene.
- **Gjengi:** `slv__salgslinje` → «Union av» → «Legg til tabell». Skriv `kvitteringslinje` og trykk Enter.
- **Faktisk:** Specly legger inn `brz__kalender__dag`, den øverste raden i den ufiltrerte listen. Neste gang listen
  åpnes, er søkefeltet tomt, men det gamle søket virker fortsatt, og listen kan vise «Ingen resultater funnet.»
- **Omvei:** klikk raden med musen. Skriv navnet i søkefeltet når listen er tom.
- **Rammer kurset:** modul 6 steg 4.

### 12. Klikk på tabellnavnet setter navnet i redigering [V, 24.11]
- **Status 24.11:** **åpen.** Ikke blant oppgavene som er nevnt i nattnotatene.
- **Faktisk:** gjelder både den store overskriften og den lille som står fast øverst når siden er rullet. En deltaker
  som «klikker utenfor» en celle der, kan komme til å døpe om tabellen. Escape tar en ut.
- **Rammer kurset:** modul 5 og 6, som nå ber deltakeren klikke i sidepanelet til venstre.

### 13. «Hent inn»: alt som er laget i Specly, blir konflikt når Git endrer det («Før: fantes ikke») [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3279 (ingen konflikt når noe laget i
  Specly senere endres i Git). Gjengivelsen under er ikke gjentatt etter rettelsen. De to «Hent inn» i modul 11 ga 0
  konflikter, men de endret ikke noe som var laget i Specly.
- **Gjengi:** lag en tabell i Specly (`gld__d__kunde`) og eksporter (i synk). Legg `description` på tabellen og
  kolonnene i kontraktfilen i Git, og push. «Hent inn til <kode>».
- **Forventet:** rene «Fra Git»-endringer. Specly har ikke endret feltene siden synkpunktet.
- **Faktisk:** 16 konflikter: 12 på `description` («Før: fantes ikke», «min: —», «Git: <teksten>») og 4 på
  `relations` (`fromColumnUuids` og `toColumnUuids`, «min —» mot «Git []»). Tabeller som kom inn fra Git tidligere
  (`gld__d__produkt` fra `fyll`), ga ingen konflikt for samme type endring.
- **Hvorfor det er alvorlig:** «Behold alle mine» kaster da ekte endringer fra Git. Tidligere notater sa «begge valg
  virker». Det gjelder bare de falske konfliktene i feil 7.
- **Omvei:** «Ta alle fra Git» → «Hent fra Git».
- **Rammer kurset:** modul 8 steg 4e (alternativet i Git), og alle steder en deltaker endrer en kontrakt i Git.
- **Prøvd på nytt 24.11 på dagtid: ikke gjengitt.** En tabell ble laget i Specly (`slv__prove`) og eksportert (i
  synk). `description` ble lagt på tabellen og to kolonner i Git, og på `brz__varius__vare` (laget i Specly i modul
  3). «Hent inn til <kode>» ga 0 konflikter. Det samme på `slv__salgslinje` og `gld__d__produkt` ga også 0. Blokken
  i modul 8 er tatt ut.

### 14. «Send inn forslag» feiler når GitHub-appen mangler «Pull requests: write» [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen** (PR #3276: norsk melding, lenke og «Prøv
  igjen» når rettigheten mangler). **Forslaget feiler fortsatt** til appen får rettigheten. Det er konfigurasjon, ikke
  en Specly-feil, og er ikke gjort. «Sendt til gjennomgang» er aldri sett.
- **Gjengi:** prosjekt koblet til GitHub via appen `specly-test-sande`. Oversikt → «Foreslå endringer» → endre en
  kolonnebeskrivelse → «Lagre endringer» → «Send inn forslag» → tittel → «Send inn».
- **Forventet:** «Sendt til gjennomgang» og en pull request.
- **Faktisk:** «Noe gikk galt: GitHub refused to open a pull request on …: the Specly GitHub App needs the "Pull
  requests: write" permission» (på engelsk i et norsk grensesnitt), to av to ganger. Branchen `forslag/…` er likevel
  pushet, og kladden står som «Kladd uten tittel» (tittelen ble ikke lagret).
- **Omvei:** åpne pull requesten for hånd i GitHub fra branchen, slå den sammen, «Hent inn», og «Forkast» kladden
  («Forkast» sletter også branchen).
- **Avklart 24.11:** forslag skal åpne pull request fra Specly, så appen må ha rettigheten. Vanlig eksport lager
  bare commits. (Pull requesten ble tatt ut av forslag i #3291 og lagt inn igjen i #3301 samme dag.)
- **Sett på test 24.11 kl. 16.50, uten rettigheten:** norsk melding med branchnavnet, «Åpne pull request i GitHub»
  og «Prøv igjen», og tittelen beholdt. Veien med rettigheten («Sendt til gjennomgang») er ikke sett.
- **Rammer kurset:** modul 8 steg 6, som nå beskriver dette som den vanlige veien.

### 15. Kladden etter et mislykket forslag kan ikke åpnes [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3278 (kladd og sammenligning for
  forslag).
- **Faktisk:** lenken «Forslag fra … (Kladd)» under tabellnavnet i Oversikt gir «Sammenligning – Sammenligningen
  kunne ikke bygges. Prøv igjen», og banneret for forslag forsvinner til siden lastes på nytt. Et klikk på kladden i
  «Mine forslag» gjør ingenting.
- **Rammer kurset:** modul 8 steg 6, bare etter feil 14.

### 16. «Hent inn» dobler reglene på forretningsbegreper som er laget i Specly [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen etter sammenslåingen.** PR #3284 (én
  begrepsregel per innhold, og doble regler ryddes). Feilen kom ikke i modul 11 (2, 2, 2 og 1 regler før og etter to
  «Hent inn», kl. 02.38), men det var før oppgaven ble startet kl. 02.40. Se merknaden i innledningen.
- **Gjengi:** lag et begrep med to regler i Specly, og eksporter (i synk). Push en hvilken som helst commit til Git.
  «Importer fra Git» → «Hent inn til <kode>» → (konfliktsiden) → «Hent fra Git». Åpne begrepet.
- **Forventet:** «Regler (2)».
- **Faktisk:** «Regler (4)»: hver regel står to ganger. Butikk, Produkt og Medlemsnivå fikk 4, Salgsbeløp 2. De nye
  reglene har id-er utledet av innholdet (versjon 5-UUID), de gamle har tilfeldige id-er. På konfliktsiden står begge
  settene under «Endringer på bare én side». «Mine endringer» viser ingenting, fordi filen blir lik.
- **Trolig årsak [A]:** begrepsfilen har ingen id per regel, så regler lest fra Git får en ny id og gjenkjennes ikke.
- **Følge:** «Regler (N)» stemmer ikke med det modul 9 sier. Koblingene ble ikke doble (6 koblede kolonner på Butikk
  hele veien).
- **Omvei:** la dem stå, eller slett duplikatene for hånd (søppelbøtta på regelen → «Slett regel» → «Slett»). Om de
  kommer tilbake ved neste «Hent inn», er ikke sett.
- **Natttesten, modul 11:** ikke sett. Butikk, Medlemsnivå, Produkt og Salgsbeløp hadde 2, 2, 2 og 1 regler før og
  etter to «Hent inn».
- **Rammer kurset:** ikke lenger. Merknadene `OMVEI-DOBLE-REGLER` er tatt ut.

### 17. En tabell som tas ut av `tables` i ODPS-filen i Git, blir stående i dataproduktet [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** Oppgaven «dataproduktmedlem fjernet i
  Git» stoppet på ukegrensen, ble startet på nytt kl. 07.20 og står i «done». PR-nummeret står ikke i nattnotatene.
  Forbeholdet `OMVEI-ODPS-TABELLER` står i modul 10 til det er klikket.
- **Gjengi:** lag et dataprodukt i Specly med fem tabeller, og eksporter. Fjern `- gld__d__dato` fra
  `customProperties.tables` i `specly/DataProducts/Salg.odps.yaml`, og push. «Hent inn til <kode>» (listen sier
  «Salg.gld__d__dato SLETTET») → «Hent fra Git».
- **Forventet:** dataproduktet har fire tabeller, og «Mine endringer 0».
- **Faktisk:** fem tabeller. «Mine endringer» viser «Salg E – Tas med: dataprodukt i gld__d__dato», og neste eksport
  skriver tabellen tilbake i filen. Endringen fra Git blir stille overkjørt. På konfliktsiden sto medlemskapet som en
  ensidig «min»-endring (`dataProductTables`, «fantes ikke → …»).
- **Trolig årsak [A]:** som feil 13: det som er laget i Specly, regnes som en ueksportert endring og vinner.
- **Ikke prøvd:** å legge en tabell til via `tables`, og det samme for et dataprodukt som kom fra Git.
- **Rammer kurset:** modul 10 steg 5 (svaret om medlemskap). Forbeholdet er merket `OMVEI-ODPS-TABELLER` (se
  `docs/kursholder.md`).

### 18. Konflikter på `replacedText` og `previousValues` ved hver «Hent inn» etter modul 9 [V, 24.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen etter sammenslåingen.** PR #3285 (feltene
  sammenlignes ikke med Git). Konfliktene kom ikke i modul 11 (0 konflikter i to «Hent inn», kl. 02.38), men det var
  før oppgaven ble startet kl. 02.40. Se merknaden i innledningen.
- **Gjengi:** koble kolonner til et begrep med «Overskriv» i dialogen «Bruk regler», og endre teksten på begrepet én
  gang. Eksporter. Push en commit til Git, og «Hent inn til <kode>».
- **Faktisk:** konfliktsiden med 6 konflikter: `replacedText` på fem koblinger (`businessConceptLinks`, «min» er for
  eksempel `{"businessDescription":"Butikkens nummer."}`) og `previousValues` på begrepet Butikk
  (`businessConcepts`). «Før: fantes ikke», «Git: —». Feltene finnes bare i Specly (teksten en kolonne hadde før
  begrepet overskrev den), så Git-siden er alltid tom.
- **Forventet:** feltene er ikke med i sammenligningen.
- **Hvorfor det er alvorlig:** her er «Behold alle mine» riktig, mens «Ta alle fra Git» er riktig for feil 13. En
  deltaker kan ikke se på knappene hvilken som gjelder. Hva «Ta alle fra Git» gjør med tekstene, er ikke prøvd.
- **Omvei:** «Behold alle mine» → «Hent fra Git».
- **Natttesten, modul 11:** ikke sett. Første «Hent inn» etter modul 9 og 10 ga 0 konflikter.
- **Rammer kurset:** kan ramme «Hent inn» etter modul 9. `moduler/start.md` har regelen og en egen rad i tabellen.

### 19. «+ datatype» i dialogen «Opprett kolonne med oppstrøm» gjør ingenting [V, 24.11]
- **Status 24.11:** **åpen.** Ikke blant nattens oppgaver.
- **Gjengi:** åpne en bronzetabell → «Legg til ny kolonne fra oppstrømstabell» → søk `raw__lagra` → hak av `item_no`
  → klikk «+ datatype» på raden til høyre.
- **Forventet:** en liste med datatyper.
- **Faktisk:** ingenting skjer (ett forsøk).
- **Omvei:** sett datatypen i kolonnen «Datatype» i tabellen etterpå.
- **Rammer kurset:** modul 3 og 11, som begge sier det.

### 20. Dialogen «Bruk regler» viser en unntakskolonne uten navn [V, 24.11]
- **Status 24.11:** **åpen.** Sett i modul 11, etter den siste Devly-chatten. Ikke meldt.
- **Gjengi:** «Hent inn» en sølvtabell fra Git der to kolonner treffer begrepsregler → regeldialogen → hak av
  «Begrepsregler» → «Kjør valgte».
- **Faktisk:** gruppen «Kolonner som allerede er unntak 1» har én rad som bare viser «. · Forretningsbeskrivelse».
  Ti minutter senere, via «Bruk alle regler», viste gruppen fire rader med navn.
- **Rammer kurset:** modul 11 steg 4. Løsningen nevner det. Lav alvorlighet.

### 21. «Avvik» på tabellen viser ikke at tabellbeskrivelsen mangler [V, 24.11]
- **Status 24.11:** **åpen.** Sett i modul 11, etter den siste Devly-chatten. Ikke meldt.
- **Faktisk:** «Avvik (22)» listet Eier, Granularitet og to linjer per kolonne. Kursets forhåndssjekk stopper i
  tillegg med «Tabellen har ingen beskrivelse, så den får ingen COMMENT i Databricks».
- **Merk [A]:** kan være med vilje. Kravet ligger i kursets forhåndssjekk, ikke i `table_types.json`. Da er det en
  sak for kurset: kravet finnes ett sted og vises et annet.
- **Rammer kurset:** modul 11 steg 5b (og modul 8). Modul 11 sier det.

### 22. Kortet «Standardkolonner» under «Massekjøring» viser foreldet tall [V, 23.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3262 (kortet henter tallet på nytt
  etter andre massekjøringer).
- **Gjengi:** fem tabeller uten type med navn `raw__…`. «Import og eksport» → «Massekjøring» → «Tabelltype auto-tag»
  → «Kjør» → «Kjør» («Tilordnet 5»).
- **Forventet:** kortet «Standardkolonner» rett under viser «5 tabeller mangler standardkolonner» og en aktiv «Kjør».
- **Faktisk:** «0 tabeller mangler standardkolonner» og grå knapp, til siden lastes på nytt.
- **Rammer kurset:** modul 2 steg 2 (den raskeste veien til standardkolonnene). Kortet er ikke prøvd som erstatning
  for «Opprett manglende» (`docs/kursholder.md`).

### 23. Kildesystem-siden oppdaterer ikke tabellisten etter «Auto-tagg tabeller» [V, 23.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3264. Årsaken var at test kjører to
  sync-replikaer, og at tabell-deltaer bare gikk til den ene. De sendes nå til alle.
- **Gjengi:** på siden for et kildesystem med mønster satt: «Auto-tagg tabeller» → bekreft («Tilordnet 5»).
- **Faktisk:** alle fem tabellene står fortsatt med «Legg til +» til siden lastes på nytt.
- **Rammer kurset:** modul 2 steg 4. Lav alvorlighet.

### 24. Eksporten skriver JSON-registerfilene under `Config` om i ny rekkefølge [V, 23.11]
- **Status 24.11:** **rettet i Specly 24.11, ikke kontrollert på skjermen.** PR #3263 (eksporten beholder
  rekkefølgen filen har i Git).
- **Faktisk:** eksporten skrev hele `specly/Config/source_systems.json` om (49 linjer inn, 22 ut) for to endrede
  kildesystemer.
- **Rammer kurset:** modul 2 og utover: støy i diffen når deltakeren ser på commiten.

## Friksjon som gjør kurset tyngre

| # | Hva | Sett | Rammer modul | Status 24.11 |
|---|---|---|---|---|
| 7 | Tallene under «Mine endringer» (fane, liste, knapp) stemmer ikke med hverandre | 21.11 | 2 og utover | Åpen |
| 8 | «Genererte filer» (`specly/.specly/specly.py`, `AGENTS.md`) står i listen og må hakes av ved hver eksport. 24.11: `specly/AGENTS.md` sto ferdig haket av i modul 8 («Speclys versjon er nyere enn den i Git»), og fem filer i modul 9 (også `specly/README.md` og `specly/.specly/specly.py`) | 21.11 | 2 og utover | Åpen |
| 9 | Søket i «Legg til kolonne fra oppstrøm» leter i kolonnenavn, ikke tabellnavn. `silver__dato` gir bare nøklene. 24.11: søket treffer tabellnavnet | 21.11 | | Rettet før natttesten, sett virke 24.11 |
| 10 | Første klikk på blyanten i «Oppstrømskolonne» rett etter valgt datatype gjør ingenting. 24.11: virket på første klikk | 21.11 | | Rettet før natttesten, sett virke 24.11 |
| 11 | Begrepsregler finner ikke kolonner som har fått nytt navn (`kundegruppekode`). Ikke prøvd 24.11 | 21.11 | 9 | Åpen, ikke prøvd 24.11 |
| 12 | Nye kolonner fra grensesnittet legges alltid sist, etter systemkolonnene (`sys__…`). Finnes fortsatt (sett 24.11) | 17.11 | 3, 4, 5 | Åpen |
| 13 | Et diagram kan ikke opprettes rett i en mappe | 21.11 | 4 | Åpen, ikke prøvd 24.11 |
| 14 | Join-type står ikke i «Opprett relasjon», bare i «Rediger relasjon». 24.11: fant ikke noe felt for Join-type i «Rediger relasjon» heller | 21.11 | 5 (tatt ut av løsningen) | Åpen |
| 15 | Datatype endres ikke nedstrøms når den endres oppstrøms (kan være meningen) | 17.11 | 3 | Åpen |
| 16 | Dialogen «Slett …?» sa at diagrammer ville forsvinne, men ingen var endret | 17.11 | | Åpen, ikke prøvd 24.11 |
| 17 | En ny branch viser 0 diagrammer og 0 dataprodukter i et par sekunder | 21.11 | 0 | Åpen, ikke prøvd 24.11 |
| 18 | Cellen «Oppstrømskolonne» tegner tekst oppå tekst når en kolonne har mange kilder (`belop`) | 24.11 | 6 | Åpen |
| 19 | Cellen «Beregning» viser bare slutten av en lang tekst etter lagring | 24.11 | 4, 6 | Åpen |
| 20 | Når en celle lagres, kan siden rulle og radene flytte seg, så neste klikk treffer feil | 24.11 | 4, 5, 6 | Åpen |
| 21 | «Fra Git» viser kolonnenavn med små bokstaver under «Sist felles» (`receiptno`) | 24.11 | 6 | Åpen |
| 22 | `specly.py check` gir rundt 150 advarsler om manglende beskrivelse i et vanlig kursprosjekt | 24.11 | 6 | Åpen |
| 23 | «+ Opprett ny tabell»: navnet står ikke (eller ikke lenge) åpent for skriving. Skriver man etter et par sekunder, heter tabellen «Ny tabell 1» | 24.11 | 7 | Rettet i Specly 24.11 (PR #3274), ikke kontrollert på skjermen |
| 24 | Linjen for massehandlinger: den røde «Slett valgte» flytter seg når «Velg verdi…» kommer og linjen brytes i to | 24.11 | 8 | Åpen. Kan være med i småting-PR #3277 [A], ikke kontrollert |
| 25 | Feltet for tabellbeskrivelse sier «Skriv inn beskrivelse (valgfri)» også når Beskrivelse er påkrevd for tabelltypen | 24.11 | 8 | Åpen. Kan være med i småting-PR #3277 [A], ikke kontrollert |
| 26 | Matrisen «Metadatafelt» → «Tabelltyper» viser ODCS-felt `properties[].customProperties` for Beskrivelse og Utviklernotat, som skrives til `description` og `transformDescription` | 24.11 | 8 | Åpen. Kan være med i småting-PR #3277 [A], ikke kontrollert |
| 27 | I dialogen «Opprett kolonne med oppstrøm» står kolonner som alt er kilde til noe, med «i tabellen». De kan velges likevel | 24.11 | 7 | Åpen |
| 28 | Dialogen «Bruk regler» viser ikke teksten som står på kolonnen (bare `tabell.kolonne · Forretningsbeskrivelse`), så «Behold» eller «Overskriv» velges blindt. Den lister heller ikke kolonner uten beskrivelse | 24.11 | 9 | Rettet i Specly 24.11 (PR #3280), ikke kontrollert på skjermen |
| 29 | «Rediger» på forretningsbeskrivelsen setter markøren først i teksten | 24.11 | 9 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 30 | Datatype på et begrep må lagres med «Lagre» etter valg i listen. På en kolonne lagres den ved valg | 24.11 | 9 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 31 | Rekkefølgen på `rules` i begrepsfilen er ikke stabil (`order: 1` før `order: 0` i `Produkt.md`, omvendt i `Butikk.md`). Ikke sett snu mellom to eksporter | 24.11 | 9 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 32 | Dataproduktet står som «Ikke på branch» i Oversikt (listen, produktsiden og «Hvor står dataproduktet mitt?»), og samtidig som «Live» under «Hva er live nå?» | 24.11 | 10 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 33 | Begrensninger vises i en boks på tre linjer, også i lesemodus. Leseren ser ikke slutten uten å rulle inne i boksen | 24.11 | 10 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 34 | Linjen «Ikke konfigurert: Påkrevd, Unik mangler et koblet flagg, så kontrakten lastes ned uten disse feltene. Åpne ODCS-oppsett» står under navnet på hvert dataprodukt, også i lesemodus. Den ser ut som en feil, og gjelder bare nedlasting | 24.11 | 10 | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 35 | Linjen «N endringer på main» øverst i menyen under «Import og eksport» skyver valgene ned når Git har nye commits. Et klikk på «Importer fra Git» kan treffe «Importer fra Fabric» | 24.11 | alle med «Hent inn» | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 36 | `specly/Config/persons.json` blir liggende som `[]` etter at siste person er slettet | 24.11 | | Åpen. Kan være med i småting-PR #3282 [A], ikke kontrollert |
| 37 | Beskrivelsen følger ikke med når en kolonne lages fra en oppstrømskolonne («Opprett N kolonner»), heller ikke for rene kopier i gull. Gir ni tomme påkrevde felt i modul 11 | 24.11 | 8, 11 | Åpen |
| 38 | Dialogen «Opprett kolonne med oppstrøm» lukker seg ikke etter «Opprett N kolonner». Den viser «Opprettet nettopp: …» og venter på «Lukk» | 24.11 | 3, 11 | Åpen |
| 39 | Enter i en navne- eller nedstrømscelle lagrer, men cellen blir stående som et åpent felt med ramme til du klikker et annet sted | 24.11 | alle | Åpen |

Ikke gjengitt 24.11: at de siste tegnene av en lang tekst i feltet Begrensninger på et dataprodukt mangler (sett i en
tidligere klikktest). 331 tegn skrevet i ett strekk kom med i feltet, på eksportsiden og i filen. Prøvd én gang.
Advarselen er tatt ut av modul 10.

Verdt å vite, ikke en feil: når et begrep slettes, beholder kolonner som ikke hadde tekst før koblingen, den arvede
beskrivelsen (dialogen sier det). Tekst en kolonne hadde før, kommer tilbake.

## Ønsker fra kurset (ikke feil)

| # | Ønske | Hvorfor |
|---|---|---|
| Ø1 | **Lag bronze-tabell fra raw med ett valg**: alle kolonner med oppstrøm, samme navn og type | Bronze er 1:1 med raw. Med dette kan modul 3 gjøres helt i Specly uten mange klikk |
| Ø2 | **Union av tabeller** beskrevet på tabellnivå, og kolonner med oppstrøm fra hver kilde | Modul 6 (kasse og nettbutikk i samme sølvtabell) |
| Ø3 | **Flagget «Eget navn»** godtatt der en kolonne bevisst avviker fra nedstrømsnavnet | Modul 4 (`aktornummer` blir `butikknummer` og `leverandornummer`). Kan løses i prosjektoppsettet med et flagg, uten endring i Specly |

## Neste steg
1. Klikk gjennom det som står som «rettet i Specly 24.11, ikke kontrollert på skjermen»: feil 8, 11, 13, 14, 15, 16,
   17, 18, 22, 23 og 24, og friksjon 23 og 28. Gjengi-stegene står under hver feil. For feil 14 og 15: les meldingen etter «Send inn» og før den inn i modul 8 steg 6
   punkt 5.
2. Gjør kontrollen for feil 7 i `docs/kursholder.md` («Konfliktsiden: «kan komme»-blokkene»), og ta blokkene ut av
   kurset hvis siden ikke kommer.
3. Når feil 17 er sett virke, fjernes omveien `OMVEI-ODPS-TABELLER` i modul 10.
4. Meld de åpne feilene som fortsatt rammer kurset (3, 4, 12, 19, 20 og 21), eller la teksten i modulen stå.
