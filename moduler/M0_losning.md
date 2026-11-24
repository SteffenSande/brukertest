# Modul 0: Løsning

## Slik skal det se ut når du er ferdig

| Hvor | Hva du ser |
|---|---|
| GitHub | Et privat repo på din konto, laget fra malrepoet, med `specly/`, `maler/`, `kilder/`, `databricks/` |
| GitHub, Settings → Integrations | Specly-appen er installert med tilgang til bare dette repoet |
| Specly | Ditt prosjekt, koblet til repoet. «Admin» har seks statuser (tre for tabeller, tre for kolonner), fire flagg, fem tabelltyper og sju datatyper, og banneret om ODCS-oppsettet er borte. Git-siden sier «I synk: Specly og main er like.» og viser «Mine endringer 0» og «Fra Git 0», uten melding om eldre format |
| Databricks, Catalog | `workspace` → `toppfart` → volumet `landing` med mappene `kalender`, `kassio`, `lojal`, `lagra`, `nettora`, `varius` |
| Databricks, Catalog | Kildetabellene til importen i modul 2: ett skjema per kilde, `toppfart_kilde_varius` (`vare`, `varegruppe`, `aktor`), `toppfart_kilde_kassio` (`kvittering`, `kvitteringslinje`) og de fire andre kildene. Det er views over filene i `landing` |

## Tallene

| Hva | Antall |
|---|---|
| Filer i `landing` til sammen | 457 |
| `landing/varius/vare/` | 3 filer (uttrekk 1. august, 1. september, 1. oktober) |
| `landing/kassio/kvittering/` | 92 filer |
| `landing/kalender/dag/` | 1 fil |

## Svar på «Hva tror du?»

457 filer: kassen 184 (to filer per dag, kvittering og kvitteringslinje), nettbutikken 92, kundeklubben 92,
lagersystemet 79 (ingen telling på søndager), varesystemet 9 (tre tabeller, ett fullt uttrekk per måned) og
kalenderen 1.

## Typiske problemer

| Du ser | Hva det betyr | Gjør |
|---|---|---|
| Specly sier at du ikke administrerer installasjonen | Repoet ligger i en organisasjon der du ikke kan installere apper | Lag repoet på din egen konto, eller be eieren av organisasjonen (eller kursholderen) koble prosjektet |
| Specly sier at installasjonen er koblet til en annen organisasjon i Specly | Appen er installert på kontoen din fra en annen Specly-organisasjon | Si fra til kursholderen |
| Listen over repoer er tom | Appen fikk ikke tilgang til repoet | På GitHub: Settings → Applications → Specly → legg til repoet |
| «Git har filene i et eldre format» og «Innstillingene … er ikke som i filene i Git» på Git-siden | En av ODCS-innstillingene fra steg 5 er ikke satt | Ikke eksporter. Rett innstillingen meldingen nevner (steg 5), og åpne Git-siden på nytt |
| Banneret «Dette prosjektet skal følge ODCS, men oppsettet er ikke kjørt ennå» står fortsatt i «Admin» | Du har ikke trykket «Oppsettet er gjort» (steg 5, punkt 4) | Kontroller de fire innstillingene, og trykk «Oppsettet er gjort» |
| «Admin» er tomt etter at prosjektet er laget | Prosjektet er ikke koblet ennå | Riktig. Oppsettet kommer når du kobler til repoet i steg 4 |
| 0 diagrammer og 0 dataprodukter rett etter at prosjektet åpnet | Tallene lastes | Vent et par sekunder |
| `databricks auth login` åpner ikke nettleseren | CLI-en finner ikke arbeidsflaten | Kjør `databricks auth login --host <adressen til arbeidsflaten> --profile kurs` |
| `./kurs oppsett` eller `./kjor` stopper med `SCHEMA_ALREADY_EXISTS` | Skjemaet er laget av notebooken `kurs_oppsett` (nettlesersporet). Terminalsporet vil lage skjemaet selv | Enklest: fortsett i nettlesersporet. Vil du over til terminalen, og pipelinen «Specly-kurs toppfart (notebook)» ikke finnes under Jobs & Pipelines: kjør de to `databricks bundle deployment bind`-kommandoene som står i feilmeldingen, og så kommandoen på nytt. Filene i volumet blir liggende |
| En notebook stopper med «Skjemaet … har allerede pipelinen «Specly-kurs toppfart» fra terminalsporet» | Du har kjørt `./kjor` i terminalen for dette skjemaet. En tabell kan bare eies av én pipeline | Ingenting er endret. Fortsett i terminalsporet, eller bruk et annet skjema i nettlesersporet: kjør `kurs_oppsett` med det nye navnet i «Skjema» først (modul 0, steg 6, «Les mer: et annet skjema enn `toppfart`»). Notebooken `kurs_sjekk` virker uansett |
| Notebooken har ingen felt for katalog, skjema eller modul | Den er ikke kjørt ennå. Feltene kommer etter første kjøring | Kjør den én gang med «Run all». Feltene ligger så i sidepanelet «Parameters» («Show parameters»). Vil du sette feltene før første kjøring (et annet skjema): kjør bare cellen «Feltene» med ▶ først |
| «Run all» gjør ingenting rett etter at du har endret et felt, og utskriftene er de gamle | Databricks kjørte cellen som leser feltene på nytt av seg selv, og «Run all» avbrøt den («Cancelled») | Vent til «Run all»-knappen er tilbake (det står «Interrupt» imens), og trykk igjen |
| `kurs_generer_kjor` stopper med «Modellen har ingen tabeller ennå» (`./generer` skriver det samme) | Det ligger ingen kontrakter i `specly/Tables`: du har ikke eksportert fra Specly ennå, eller ikke hentet eksporten | Eksporter fra Specly (modul 2, steg 3a), «Pull» i Git-mappen (terminalsporet: `git pull`), og kjør på nytt |
| Git-vinduet i Databricks viser en notebook (`notebooks/kurs_….py`) som endret, uten at du har endret noe | Databricks skrev linjene øverst i filen (`# /// script` … `# ///`) på nytt da notebooken ble kjørt på serverless, for eksempel med et annet versjonsnummer enn det som står i kursets filer | Ufarlig. La den bli med i neste «Commit & Push» |
| «Pull» i Git-mappen stopper med «Resolve conflict(s) before merge» i en notebookfil | Filen er endret både hos deg og i GitHub | Trykk «Abort» og «Confirm». I listen «Changes»: trykk på de tre prikkene ved notebookfilen og velg «Discard changes». Gjør så «Pull» på nytt |
| Rød tekst når en notebook starter («Note: you may need to restart the kernel …», eller om «pip's dependency resolver» og `mlflow-skinny`) | Data Contract CLI installeres og bytter ut noen pakker. Notebooken starter Python på nytt selv | Ingenting |
| Pipelinen feiler med `UNSUPPORTED_LIBRARY_FILE_TYPE` om `tabeller/.gitkeep` | Repoet ble laget fra en eldre utgave av malrepoet, der generatoren lot `.gitkeep` ligge | Slett `databricks/pyspark/tabeller/.gitkeep`, commit og push, og kjør igjen |
| `./kurs oppsett` stopper med en feil om tilgang | Brukeren din kan ikke lage skjema i katalogen | I Databricks Free skal det virke i `workspace`. Ellers: be om et skjema du kan bruke, og sett `SKJEMA` |
