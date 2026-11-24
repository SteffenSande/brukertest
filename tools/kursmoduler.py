"""Hvilken modul hver tabell i fasiten hører til, og hva `./kurs fyll` legger inn. Ett sted, brukt av
tools/startpunkter.py (startpunktene), tools/kurs.py (til, fyll, sjekk) og tools/test_fasit_lokalt.py (--modul).

Kjerneløpet er modul 2-5. Kalenderen tas inn i modul 5, fordi den først trengs
av datodimensjonen. Derfor står raw__kalender__dag, brz__kalender__dag og slv__dato under modul 5, ikke under
modul 2, 3 og 4.

«Modellerer, videre» er modul 6, 7 og 11. Modul 8-10 (styring, begreper, dataprodukt) legger ikke til
tabeller, men endrer prosjektoppsettet og kontraktene, og har egne startpunkter. Startpunktet før en modul er alt fra
modulene med lavere nummer: start/M8 = fasit/M7, og start/M11 = fasit/M10 (med nettbutikken, kunden, styringen,
begrepene og dataproduktet). Modul 11 trenger bare modul 5 (produkt, butikk og kalender), men startpunktene er én
kjede, så den som tar sporet 6-11 fortsetter rett på, og den som kommer fra modul 5, får 6-10 med `./kurs til M11`.

specly/ er den fulle modellen (fasit for den siste modulen). Startpunktene før en modul tar bort det modulen legger
til (tools/startpunkter.py). Det som skal tas bort, står her.
"""
import filecmp
import os
import shutil
import tempfile
import zipfile

# Tabellene som er ferdige ved slutten av hver modul (i tillegg til tabellene fra modulene før).
TABELLER_PER_MODUL = {
    2: ["raw__varius__vare", "raw__varius__varegruppe", "raw__varius__aktor",
        "raw__kassio__kvittering", "raw__kassio__kvitteringslinje"],
    3: ["brz__varius__vare", "brz__varius__varegruppe", "brz__varius__aktor",
        "brz__kassio__kvittering", "brz__kassio__kvitteringslinje"],
    4: ["slv__butikk", "slv__leverandor", "slv__salgslinje", "slv__produkt", "slv__produktgruppe"],
    5: ["raw__kalender__dag", "brz__kalender__dag", "slv__dato",
        "gld__d__produkt", "gld__f__salg", "gld__d__butikk", "gld__d__dato"],
    6: ["raw__nettora__ordrelinje", "brz__nettora__ordrelinje"],
    7: ["raw__lojal__medlem", "brz__lojal__medlem", "slv__kunde", "gld__d__kunde"],
    # Modul 8-10: ingen nye tabeller. Hva de endrer, står under (STYRING_I_MODUL, BEGREPER_I_MODUL, DATAPRODUKT_I_MODUL).
    8: [],
    9: [],
    10: [],
    11: ["raw__lagra__beholdning", "brz__lagra__beholdning", "slv__lagerbeholdning", "gld__f__lagerbeholdning"],
}

# Tabellene modulteksten IKKE ber deltakeren lage selv. `./kurs fyll M<n>` legger dem inn fra fasit/M<n>.
# Modul 5: gld__d__butikk og gld__d__dato. gld__d__dato bygger på slv__dato, som bygger på
# kalenderen, og modul 5 ber ikke deltakeren lage kalenderkjeden. Den følger derfor med. Har deltakeren allerede
# laget en av tabellene (for eksempel importert kalenderen selv), lar fyll den være.
# Modul 3: deltakeren lager brz__varius__vare grundig og de to kassetabellene (modul 4 bygger videre på dem). De to
# andre varius-tabellene er samme håndverk en gang til, og legges inn (ikke klikk det samme fem ganger).
# Modul 6: deltakeren lager raw via Git (kopi av en kontrakt) og unionen i sølv. Bronze er samme håndverk som i modul 3, og
# legges inn (moduler/M6.md steg 2).
# Modul 7: kundeklubbens raw og bronze er samme håndverk som i modul 2 og 3. Deltakeren lager slv__kunde, fb__slv__kunde,
# gld__d__kunde (SCD2) og fk__gld__d__kunde, som er det modulen handler om.
# Modul 11: deltakeren lager raw (Parquet) og bronze (BK uten dato) og faktaen. slv__lagerbeholdning er en enkel
# sølvtabell som i modul 4.
FYLL = {
    3: ["brz__varius__varegruppe", "brz__varius__aktor"],
    4: ["slv__produkt", "slv__produktgruppe"],
    5: ["raw__kalender__dag", "brz__kalender__dag", "slv__dato", "gld__d__butikk", "gld__d__dato"],
    6: ["brz__nettora__ordrelinje"],
    7: ["raw__lojal__medlem", "brz__lojal__medlem"],
    11: ["slv__lagerbeholdning"],
}

# Relasjoner som modulteksten ber deltakeren lage i en senere modul enn tabellen. Startpunktene før den modulen
# får tabellen uten relasjonene (tabell: modulen relasjonene lages i). Modul 4 steg 4: linjen peker på kvitteringen.
RELASJONER_I_MODUL = {
    "brz__kassio__kvitteringslinje": 4,
}

# Endringer i en tabell fra en tidligere modul. Startpunktene før modulen har tabellen uten endringen
# (tools/startpunkter.py). I tillegg tas alltid bort, uten at det står her: oppstrømskolonner i tabeller som ikke finnes
# i startpunktet, og tabeller i «Union av» som ikke finnes (feltet forsvinner når færre enn to er igjen).
# Kolonner som legges til (tabell.kolonne: modulen).
KOLONNER_I_MODUL = {
    "slv__salgslinje.salgskanal": 6,
    "slv__salgslinje.fb__slv__kunde": 7,
    "gld__f__salg.fk__gld__d__kunde": 7,
    "gld__f__salg.salg_dato": 7,
}
# Beregning (med Utviklernotat) som legges på en kolonne som fantes fra før (tabell.kolonne: modulen). Modul 6:
# etter unionen får nettbutikken butikk 107 og rabatt 0, og fb__slv__butikk regnes av butikknummer.
BEREGNING_I_MODUL = {
    "slv__salgslinje.butikknummer": 6,
    "slv__salgslinje.rabatt_belop": 6,
    "slv__salgslinje.fb__slv__butikk": 6,
}
# Tabellbeskrivelsen før modulen som endret tabellen (tabell: (modulen, beskrivelsen før)).
BESKRIVELSE_FOR_MODUL = {
    "slv__salgslinje": (6, "Salget: én rad per varelinje på en kvittering. Linjen fra kassen med tidspunkt og medlem fra "
                           "kvitteringshodet."),
}

# Modul 8 (styring): admin gjør feltene påkrevd for gull-tabelltypene (kravene i
# specly/Config/table_types.json), og forvalteren fyller ut feltene i kontraktene. Startpunktene før modul 8 har ingen
# krav og ingen verdier i feltene. Selve feltene (Eier, Klassifisering, Granularitet) er i prosjektoppsettet i alle
# startpunktene (modul 1). Verdiene står bare ett sted: i kontraktene i specly/ (moduler/M8_losning.md).
STYRING_I_MODUL = 8
STYRINGSKRAV = ("requiredFieldDefUuids", "requiredColumnFieldDefUuids")
STYRINGSFELT = ("eier", "granularitet", "klassifisering")

# Modul 9 (forretningsbegreper): fire begreper i specly/Concepts med regler. Startpunktene før modul 9 har ingen begreper.
# Kolonnene som fikk begrepets tekst («Overskriv», moduler/M9_losning.md), hadde denne beskrivelsen før
# (tabell.kolonne: (modulen, beskrivelsen før)). Kolonnene med «Behold» har sin egen tekst og et unntak i begrepsfilen.
# En kobling i en begrepsfil til en tabell som ikke finnes i startpunktet, tas bort (modul 11 kobler lagertabellene).
BEGREPER_I_MODUL = 9
KOLONNEBESKRIVELSE_FOR_MODUL = {
    "slv__butikk.butikknummer": (9, "Butikkens nummer (101-107)."),
    "slv__salgslinje.butikknummer": (9, "Butikken salget skjedde i."),
    "gld__d__butikk.butikknummer": (9, "Butikkens nummer."),
    "brz__kassio__kvittering.storeId": (9, "Butikken."),
    "brz__kassio__kvitteringslinje.storeId": (9, "Butikken."),
    "slv__produkt.varenummer": (9, "Varenummeret uten ledende nuller (4711)."),
    "slv__salgslinje.varenummer": (9, "Varenummeret uten ledende nuller."),
    "gld__d__produkt.varenummer": (9, "Varenummeret uten ledende nuller."),
    "brz__varius__vare.VARENR": (9, "Varenummeret uten ledende nuller (4711)."),
    "brz__kassio__kvitteringslinje.sku": (9, "Varenummeret uten ledende nuller."),
    "brz__nettora__ordrelinje.product_code": (9, "Varenummeret uten ledende nuller."),
    "slv__salgslinje.belop": (9, "Beløpet for linjen med mva, etter rabatt. Negativt ved retur."),
    "gld__f__salg.belop": (9, "Beløpet for linjen med mva, etter rabatt. Negativt ved retur."),
}

# Modul 10 (dataprodukt): specly/DataProducts/Salg.odps.yaml, og `dataProduct: Salg` på roten av kontraktene til tabellene
# i det (moduler/M10_losning.md). Startpunktene før modul 10 har ingen av delene. En tabell i dataproduktet som ikke finnes
# i startpunktet, tas bort fra listen. Diagrammet Salg er ikke med: startpunktene har ingen diagrammer (modul 4 og 5 lager
# dem i Specly).
DATAPRODUKT_I_MODUL = 10

# Det modul 2 steg 4 ber deltakeren fylle ut på kildesystemene. start/M2 har kildesystemene uten dette; fra
# fasit/M2 og utover står det som i specly/Config/source_systems.json.
KILDESYSTEM_I_MODUL_2 = {"varius", "kassio"}
KILDESYSTEM_FELT_I_MODUL_2 = ("metadataValues", "regexPattern")

MODULER = sorted(TABELLER_PER_MODUL)

# Det `./kurs til` og notebooks/kurs_til henter fra startpunktet (stier under specly/): modellen (tabellene, begrepene
# fra modul 9 og dataproduktet fra modul 10), kildesystemene (modul 2) og tabelltypene (kravene fra modul 8). Resten av
# specly/Config, .specly.json og .specly/ er knyttet til ditt Specly-prosjekt, og endres ikke.
FRA_STARTPUNKTET = ("Tables", "Concepts", "DataProducts", "Config/source_systems.json", "Config/table_types.json")

_ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARKIV = os.path.join(_ROT, ".startpunkter")
_utpakket = {}


def arkivfil(type_, m):
    """.startpunkter/<start|fasit>-M<n>.startpunkt (en zip-fil). Startpunktene ligger pakket, fordi Specly leser alle
    .odcs.yaml i repoet som kontrakter: løse kopier med de samme id-ene får Specly til å holde tilbake endringer fra Git.
    Filene heter ikke .zip, fordi Databricks pakker ut .zip-filer når en mappe lastes opp til arbeidsflaten (prøvd:
    alle åtte havnet i én mappe, og notebookene fant ingen startpunkter)."""
    return os.path.join(ARKIV, f"{type_}-M{int(str(m).lstrip('Mm'))}.startpunkt")


def startpunkt_mappe(type_, m):
    """Pakker ut startpunktet til en midlertidig mappe og gir stien til specly/ der. None når det ikke finnes."""
    fil = arkivfil(type_, m)
    if not os.path.isfile(fil):
        return None
    if fil not in _utpakket:
        mappe = tempfile.mkdtemp(prefix=f"startpunkt-{type_}-M{int(str(m).lstrip('Mm'))}-")
        with zipfile.ZipFile(fil) as z:
            z.extractall(mappe)
        _utpakket[fil] = os.path.join(mappe, "specly")
    return _utpakket[fil]


def tabeller_til_og_med(modul):
    """Alle tabellene som finnes ved slutten av modulen (fasit/M<modul>). Modul 1 og lavere: ingen. Virker for alle
    nummer, også de uten tabeller: tabeller_til_og_med(10) er tabellene fra modul 2-7."""
    return [t for m in MODULER if m <= modul for t in TABELLER_PER_MODUL[m]]


def modul_for(tabell):
    for m, tabeller in TABELLER_PER_MODUL.items():
        if tabell in tabeller:
            return m
    return None


def _filer(specly):
    """{sti under specly/: full sti} for filene i FRA_STARTPUNKTET."""
    ut = {}
    for del_ in FRA_STARTPUNKTET:
        sti = os.path.join(specly, del_)
        if os.path.isfile(sti):
            ut[del_] = sti
        for mappe, _, filer in os.walk(sti):
            for f in filer:
                if f != ".DS_Store":
                    ut[os.path.relpath(os.path.join(mappe, f), specly)] = os.path.join(mappe, f)
    return ut


def det_som_endres(kilde, specly):
    """Filene i specly/ som `bytt_til` sletter eller skriver over: [(sti under specly/, «slettes» eller «overskrives»)]."""
    nye, har = _filer(kilde), _filer(specly)
    return [(sti, "slettes" if sti not in nye else "overskrives") for sti in sorted(har)
            if sti not in nye or not filecmp.cmp(har[sti], nye[sti], shallow=False)]


def bytt_til(kilde, specly):
    """Gjør FRA_STARTPUNKTET i specly/ lik startpunktet i `kilde`. En mappe kopieres først ved siden av og byttes til
    slutt, så den aldri blir borte halvveis. Har ikke startpunktet mappen, blir Tables tom og de andre fjernes."""
    for del_ in FRA_STARTPUNKTET:
        fra, til = os.path.join(kilde, del_), os.path.join(specly, del_)
        if os.path.isfile(fra):
            shutil.copy2(fra, til)
            continue
        ny = til + ".ny"
        shutil.rmtree(ny, ignore_errors=True)
        if os.path.isdir(fra):
            shutil.copytree(fra, ny)
        elif del_ == "Tables":
            os.makedirs(ny)
        shutil.rmtree(til, ignore_errors=True)
        if os.path.isdir(ny):
            os.rename(ny, til)
