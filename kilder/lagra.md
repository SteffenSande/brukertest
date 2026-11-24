# Kildeark: Lagra (lagersystemet, modul 11)

| | |
|---|---|
| **System** | Lagra, lagersystemet (telling per vare og butikk) |
| **Eier** | Logistikk |
| **Leveransemåte** | Fullt uttrekk av beholdningen etter dagens telling |
| **Når** | Mandag til lørdag kl. 23:00. Ingen telling på søndag |
| **Tabeller** | `beholdning` |

## Format (det koden trenger)

| | |
|---|---|
| Filformat | Parquet |
| Datoformat | ekte datotype i filen |

## Kjente svakheter
- `item_no` er varenummeret som heltall, uten ledende nuller.
- Søndager mangler. Beholdningen en søndag er lørdagens telling.
