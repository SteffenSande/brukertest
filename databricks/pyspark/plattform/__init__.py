"""Funksjonspakken de genererte tabellfilene kaller. Generisk: ingen funksjon nevner en tabell eller kolonne ved navn.

Modulene i den rekkefølgen dataene går gjennom dem:
  felles     kolonnelisten fra kontrakten (Kolonne, ddl, velg), les_tabell, kopi, tom, beregn, med_beregninger,
             nøkler (nokkel_av …)
  raw        les_landingsfiler, landingssone
  bronze     rensefunksjonene, Kildeformat, cast_til (den ene cast-funksjonen), Rens, rens_og_cast
  historikk  lag_historikk (SCD2 fra leveransene)
  solv       Kobling, sett_sammen_over_tid, Gren, sett_sammen_union
  gull       lag_dimensjon, Oppslag, med_spesialrader, gjeldende_versjoner, oyeblikksbilde, lag_kolonner, sla_opp_nokkel,
             med_primaernokkel
  konstanter GENERERT fra maler/pyspark/plattform.j2

Etter pipelinen (ikke i den):
  tags       sett_tags: eier og klassifisering som tags i Unity Catalog (modul 8)
  tags_data  GENERERT fra kontraktene med maler/pyspark/tags.py.j2
"""
