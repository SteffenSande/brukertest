# Kildeark: Nettora (nettbutikken, modul 6)

| | |
|---|---|
| **System** | Nettora, nettbutikkplattformen (ordrelinjer) |
| **Eier** | Netthandel |
| **Leveransemåte** | Endringer: én fil per dag med gårsdagens ordrelinjer |
| **Når** | Hver dag kl. 06:00, for gårsdagen. Nettbutikken er åpen alle dager |
| **Tabeller** | `ordrelinje` |

## Format (det koden trenger)

| | |
|---|---|
| Filformat | JSON, én rad per linje |
| Desimaltegn | `.` (punktum) |
| Tidsformat | ISO 8601 i UTC |

## Kjente svakheter
- `customer_id` er alltid fylt: du må være medlem for å handle på nett.
- `price` er prisen etter rabatt.
- `product_code` har ledende nuller, som i varesystemet.
