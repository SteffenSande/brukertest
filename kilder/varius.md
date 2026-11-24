# Kildeark: Varius (varesystemet)

*Oppdiktet, som alt i kurset.*

| | |
|---|---|
| **System** | Varius, varesystemet til Toppfart Sport (varer, varegrupper, butikker og leverandører) |
| **Eier** | Innkjøp og vareforvaltning, ved teamet Vare og pris |
| **Kontakt i kilden** | Vare og pris (vare-og-pris@toppfart.example) |
| **Leveransemåte** | Fullt uttrekk: hver fil har alle radene som finnes i systemet den dagen |
| **Når** | Den 1. hver måned kl. 05:00, med alt som finnes i systemet da |
| **Tabeller** | `vare`, `varegruppe`, `aktor` |

## Format (det koden trenger)

| | |
|---|---|
| Filformat | CSV med overskriftsrad |
| Skilletegn | `;` |
| Desimaltegn | `,` (komma), for eksempel `1299,00` |
| Datoformat | `dd.MM.yyyy`, for eksempel `05.09.2026` |
| Tidssone | ikke aktuelt (ingen tidspunkt) |
| Uttrekk | `Fullt` (hver fil har alle radene) |

## Kjente svakheter
- `VARENR` har alltid seks tegn med ledende nuller (`004711`). Kassen og lageret bruker samme nummer uten nuller.
- `aktor` blander butikker (`AKTTYPE = B`) og leverandører (`AKTTYPE = L`) i samme tabell.
- Noen varer mangler `MERKE` (tom tekst).
