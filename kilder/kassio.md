# Kildeark: Kassio (kassesystemet)

| | |
|---|---|
| **System** | Kassio, kassesystemet i butikkene (kvitteringer og kvitteringslinjer) |
| **Eier** | Butikkdrift |
| **Kontakt i kilden** | Leverandøren av kassesystemet, via Butikkdrift (butikkdrift@toppfart.example) |
| **Leveransemåte** | Endringer: én fil per dag med gårsdagens kvitteringer. Ingen fil har alle kvitteringene |
| **Når** | Hver dag kl. 06:00, for gårsdagen. Søndag er butikkene stengt, og filen har bare overskriftsraden |
| **Tabeller** | `kvittering` (hodet), `kvitteringslinje` (varelinjene) |

## Format (det koden trenger)

| | |
|---|---|
| Filformat | CSV med overskriftsrad |
| Skilletegn | `,` |
| Desimaltegn | `.` (punktum) |
| Tidsformat | `yyyy-MM-dd'T'HH:mm:ssX` (ISO 8601, `Z` betyr UTC), for eksempel `2026-08-01T09:14:22Z` |
| Tidssone | UTC. Norsk dato må regnes ut |
| Uttrekk | `Endringer` (hver fil har bare gårsdagens kvitteringer) |

## Kjente svakheter
- `memberNo` er tomt når kunden ikke viser medlemskortet (rundt 40 % av kvitteringene).
- `sku` er varenummeret uten ledende nuller.
- Filer kan komme for sent. Datoen i filnavnet er når filen kom, ikke når salget skjedde.
- Det har hendt at samme linje står to ganger i en fil.
- Fra 1. oktober har kvitteringslinjen en ny kolonne, `campaignCode`.
