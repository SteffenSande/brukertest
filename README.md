# Specly-kurset: Toppfart Sport

Et opplæringskurs i datamodellering med Specly og Databricks. Du modellerer en oppdiktet sportskjede, Toppfart Sport
AS, fra rådata til stjerner i gull. Koden som bygger tabellene i Databricks, genereres fra modellen med Data Contract
CLI og Jinja-maler.

**Hva er kurset?** Se introsiden [docs/kurs-intro.html](docs/kurs-intro.html). GitHub viser HTML som kildekode: last
ned filen og åpne den i nettleseren.

## Slik starter du
1. Trykk «Use this template» → «Create a new repository» øverst på denne siden. Velg din egen GitHub-konto som eier,
   og la repoet være privat.
2. Følg [modul 0](moduler/M0.md). Den kobler repoet ditt til ditt eget Specly-prosjekt og din egen
   Databricks-arbeidsflate.

## Hva du trenger
- En GitHub-konto der du kan installere apper på dine egne repoer.
- En invitasjon til Specly fra kursholderen. Prosjektet lager du selv i modul 0.
- En Databricks-arbeidsflate. Databricks Free Edition holder.
- Et personlig tilgangstoken i Databricks til importen i modul 2, i begge spor. Modul 2 viser hvordan du lager det, og
  har en omvei hvis du ikke kan.
- Nettlesersporet: bare nettleser. Terminalsporet: `git`, `gh`, `uv`, Databricks CLI og Data Contract CLI
  (`uv tool install datacontract-cli==1.2.10`). Se modul 0. Velg ett spor og hold deg til det: de to sporene kan ikke
  dele et skjema i Databricks.

## Modulene
| # | Modul | Fil |
|---|---|---|
| 0 | Oppsett | [M0](moduler/M0.md) |
| 1 | Prosjektoppsett (valgfri, for admin) | [M1](moduler/M1.md) |
| 2 | Raw fra kilden | [M2](moduler/M2.md) |
| 3 | Bronze | [M3](moduler/M3.md) |
| 4 | Sølv | [M4](moduler/M4.md) |
| 5 | Første stjerne | [M5](moduler/M5.md) |
| 6 | Ny kilde: nettbutikken | [M6](moduler/M6.md) |
| 7 | Kunden og historikk | [M7](moduler/M7.md) |
| 8 | Dokumentasjon og styring | [M8](moduler/M8.md) |
| 9 | Forretningsbegreper | [M9](moduler/M9.md) |
| 10 | Dataprodukt | [M10](moduler/M10.md) |
| 11 | Lagerbeholdning | [M11](moduler/M11.md) |

Modul 11 er den siste, og slutter med en oppsummering av hva du har bygget, og hva kurset har laget i Databricks.

Hver modul har en løsning (`moduler/M<n>_losning.md`). Med `./kurs til M<n>` (eller notebooken `kurs_til`) kan du
starte på hvilken som helst modul fra og med modul 2. Se [moduler/start.md](moduler/start.md).
