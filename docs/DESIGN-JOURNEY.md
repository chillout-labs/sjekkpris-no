# SjekkPris – designbeta og videre arbeid

Oppdatert 18. oktober 2026. Betaen er publisert under `/beta/` og beholder
`noindex`. Dette dokumentet beskriver nåværende avgrensning; eldre daterte
reviewrapporter er historiske, ikke gjeldende publiseringsstatus.

## Bruk og verifisering

Bygg med `python tools/preview_design.py`. Server `.design-preview` lokalt.
`/designoversikt/` gir tilgang til alle designreisene. `tools/package_beta.py`
pakker betaen under `/beta/` med korrekte interne lenker og ressurser.

`python tools/capture_design.py` kontrollerer samtlige eksisterende reiser på
seks skjermbredder og tar skjermbilder. Playwright Chromium og Pillow kreves.
Internlenker, fragmenter, unike ID-er og utsatt lastede kortressurser sjekkes
også uten nettverk før publisering, både i lokalt og pakket betaoppsett.
Designarbeidsgrener under `design/` får automatisk nettleserkontrollen i CI når
relevante designfiler endres. Vanlig build/test og outputkontroll gjelder også.

## Ferdig designgrunnlag

- Felles navigasjon, søk, produktkort og responsive produkt-/kategorisider.
- Produktpresentasjon med varepris som standard og kjent/ukjent frakt eksplisitt.
- Betaeksempler på galleri, varianter, prishistorikk, spesifikasjoner og produktlenker.
- Kategoriutvalg, filtre og innsikt; merkeoversikt og merkesider.
- Guideoversikt og én lesbar TV-guide med produkt-/kategorilenker.
- Butikkoversikt og Baby Brezza-forslag, med 12 produkter per side.
- Informasjonssider, kontaktskjema, konto, favoritter, prisvarsel, sammenligning
  og assistentsvar som tydelig merkede funksjonsdemonstrasjoner.

Betaen består av 44 HTML-sider. De fleste produktene, prisene og butikkene er
fiktive. Baby Brezza-siden bruker et uttrykkelig datert offentlig øyeblikksbilde
med 15 produkter fra 18.10.2026. Den er ikke koblet til løpende butikkdata.
Produktlenkene der går til den virkelige SjekkPris-katalogen.

Det virkelige katalogbygget og betaen er separate. Virkelige kategorier,
produktbilder og merker finnes allerede når de leveres via gjeldende kontrakt.
Tidligere formuleringer om at kategorier/bilder ennå ikke er aktivert er utdaterte.

## Gjeldende beslutninger

`docs/BUTIKKSIDER-V1.md` er godkjent butikkstandard. Produkter først, maks 12
kort per side, dokumenterte butikkopplysninger og ingen direkte butikklenker
uten godkjent affiliate-destinasjon. Erfaringer for butikker og produkter er
utsatt til et eget segment. Senere brukerbeslutninger i `DESIGN_STATUS.md`
går foran eldre referanser, blant annet mobilheader og varepris som standard.

## Neste arbeid – riktig ansvar og rekkefølge

1. **Frontend:** videre kontroll av faktiske brukerreiser, tilgjengelighet,
   søke-/filtertilstand og feilretting innenfor godkjent design.
2. **Chillout-integrasjon:** godkjente butikkidentiteter, aktive produkttellinger,
   serverbasert søk/filter/paginering og destinasjonsspesifikke affiliate-lenker.
   Ingen stor butikkatalog eller komplett indeks skal sendes til nettleseren.
3. **Produktinnhold:** avtalte kilder og adaptere for ekte galleri, varianter,
   spesifikasjoner, historikk og relaterte produkter. Vis ikke fixturedata som fakta.
4. **Redaksjon:** verifiserte butikk-/merkeopplysninger, originale guider og
   personvern-/kontaktinnhold som samsvarer med faktisk drift.
5. **Separate funksjonsprosjekter:** AI, konto/synk, varsler og senere modererte
   butikk-/produkterfaringer. Dagens demonstrasjoner er ikke aktive tjenester.
6. **SEO-sporet:** videre arbeid med metadata, canonical, strukturert data og
   indekseringsregler skjer separat. Noindex beholdes inntil lansering er godkjent.

Se `DESIGN_STATUS.md` og tilhørende pull requests for faktisk test-, merge- og
publiseringsbevis. Dette er ikke en full WCAG-sertifisering eller en påstand om
at alle sider er pikselidentiske med alle historiske designreferanser.
