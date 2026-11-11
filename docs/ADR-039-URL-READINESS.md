# ADR-039 — SjekkPris URL Readiness v1

Status 23.10.2026: implementert som eksplisitt readiness-modus for gjennomgang.
Ingen ruteendring er aktivert i eksisterende bygge-/publiseringsflyt. Dette er
ikke en ferdig eller godkjent produksjons-cutover.

## Beslutningsgrunnlag og kontrollert utgangspunkt

Lest gjeldende Drive-dokumenter 23.10.2026:

- [SjekkPris Web Profile v1.0, særlig §53](https://docs.google.com/document/d/1zvSFOS-eb-c8e4MTRXmXDwISTMBzEJDNkqcjwSCBzk4/edit).
- [Architecture Decision Log, ADR-037 og ADR-039](https://docs.google.com/document/d/19D_mS5zrb8kR2GTlVDkHEKGnc485PfCk_5Snt7wCdlw/edit).
- [Chillout Web Standard v1.0](https://docs.google.com/document/d/1C1S86kk2YvKIiYD0lkRnuEruHKL95ONvLEAbARARq6A/edit).

Kontrollert `main` på `c230feb`, eksisterende kode og 87 opprinnelige tester.
Gjennomgått PR #3 (canonical/data-kontrakt), #4 (kategori/design),
#32 (butikkpaginering) og #33 (lenkekontroll/navigasjon), samt PR-oversikten.
Eksisterende produktadresse er `/p/{namespace}/{local_slug}/`; kategoriadressen
er `/kategori/{navneavledet-slug}/`, søk `/search/`. `/produkt/` er tidligere
policy, ikke en observert generell produktrute i denne koden.

## Implementert

- Opt-in `build.py --url-registry ...`: produkter `/p/{frozen-slug}/`,
  kategorier `/k/{frozen-slug}/`, søk `/sok/`.
- Delt rutekontrakt validerer også `/merke/{slug}/` og `/guide/{slug}/`.
  Produksjonsbygg har foreløpig ingen brand-/guide-innholdsadapter. Eksisterende
  syntetiske designvisninger beholdes; de blir ikke produksjonsinnhold.
- Canonical-ID fra eksisterende tilbudssvar må ha en aktiv rute i snapshotet.
  Et eventuelt ID-felt i katalogen må stemme. Oppslag til dagens tilbuds-API
  beholder namespace/local_slug; disse feltene blir ikke canonical identitet.
- Produkttitler og kategoriplassering endrer ikke frosne slugs. Identiske
  titler med forskjellige canonical-ID-er får separate sider. Flere
  katalogposter for samme canonical side avvises fremfor å blandes.
- Normalisering bevarer Pro, Plus (`+`), Ultra, XL, kapasitet, størrelse,
  årsmodell og pakningsstørrelse uten vilkårlig lengdekutt. Den brukes bare som
  hjelpefunksjon for verifisert navnegrunnlag; bygget genererer ikke slugs fra
  rå feedtitler. Verifisert disambiguering og stabile offentlige suffikser
  leveres eksplisitt i registry, ikke fra provider-ID eller build-rekkefølge.
- Chillouts leverte kategori-ID-er og ancestor-stier brukes videre. Ett
  katalogprodukt aktiverer blad og samtlige leverte foreldre. Tomme grener
  konstrueres ikke. Sykliske og inkonsistente stier avvises.
- Kort, eksempellenker, søkeindeks, kategorier og breadcrumbs bruker samme
  resolver. Delt shell får nye søk-/kategoriadresser i readiness-artefaktet.
- Én absolutt selvrefererende canonical per bygget innholdsside. Alle sider
  beholder noindex, også søk og 404. Sitemap er tomt fordi alle sidene er
  noindex. Ingen indeksaktivering eller ny ProductGroup/schema-policy.
- Valideringsport stopper feil canonical, tapt noindex, manglende lokale
  lenkemål/ankere og søkeindekslenker. Eksisterende lekkasjekontroll beholdes.
- Redirect-plan ved siden av artefaktet: eksplisitt dokumenterte gamle produkt-
  og kategoriadresser, søk/kategorioversikt og slash-normalisering.
  Eksplisitte historiske aliaser krever dokumentert evidens. Kun 301/308 til
  bygget canonical mål; 404/410 uten irrelevant etterfølger. Ingen kjeder,
  løkker, asset-shadowing eller blanket redirect til forsiden. Gamle
  katalogproduktadresser må ha et eksplisitt registry-alias; dagens kategorinavn
  brukes aldri til å gjette historisk URL-eierskap. Både med og uten avsluttende
  skråstrek peker gamle directory-adresser direkte til endelig mål.
- Tidligere eierskap reserveres ved kontrollerte navnerettelser, merges og
  fjerning. Sammenligning mot forrige snapshot hindrer resirkulering og tap
  av historiske disposisjoner. Canonical produkt-ID-er endres aldri her.

## Privat inputkontrakt (lokal v1, ikke eksisterende Chillout-API)

```json
{
  "version": 1,
  "property": "sjekkpris-no",
  "revision": "immutable-revision",
  "entities": [
    {"kind": "product", "entity_id": "CANONICAL_PRODUCT_ID", "slug": "verified-model-256-gb", "state": "active"},
    {"kind": "category", "entity_id": "CANONICAL_CATEGORY_ID", "slug": "mobiltelefoner", "state": "active"}
  ],
  "reservations": [],
  "aliases": []
}
```

`kind` er product/category/brand/guide. `state` er active eller reserved.
Ved navnerettelse beholdes gammel kind/entity_id/slug i `reservations`, og
gammel sti får et dokumentert alias med `source`, `status`, `kind`, `entity_id`
og `evidence`. Ved kjent fjerning brukes status 410 uten målfelter. Merge
reserverer gammel eierskap og peker eksplisitt til bevist overlevende entity.
Aliasene resolver alltid direkte til siste aktive rute. Ved flere godkjente
merges følges de dokumenterte identitetsetterfølgerne internt, mens den ferdige
planen har ett HTTP-hopp. Ved kjent fjerning uten etterfølger blir også gamle
beviste ekvivalente aliaser 404/410 direkte. Sykluser og udokumenterte ender
avvises; historiske registry-poster endres ikke for å flate ut planen.

Snapshot og forrige revisjon er private byggeinput, aldri en fil i nettstedet.
Frontend leser kun. Den allokerer ikke canonical identitet eller slugs og
har ingen databasekobling. Produksjon må binde korrekt revisjon til godkjent
byggesnapshot og håndheve tidligere reservasjoner hos registry-eieren.
Validering alene gir ingen publiseringstillatelse.

Readiness kjøres med `ROBOTS_NOINDEX=1` og et separat outputområde, for eksempel
`python build.py --out _url-readiness --url-registry PRIVATE.json
--previous-url-registry PREVIOUS.json` (én kommandolinje). Dagens build-time
lesetilgang til katalog og tilbud kreves fortsatt. Redirect-planen heter da
`_url-readiness.redirects.json`. Den må aldri tolkes som deployede HTTP-regler.

## URL-inventar og migreringsgrense

[URL-INVENTORY-BETA.csv](URL-INVENTORY-BETA.csv) er reprodusert fra gjeldende
lokale designbygg, inkludert eksisterende produktlenker i butikk-snapshotet.
Genereres med `tools/inventory_urls.py`; inneholder ingen nye mål gjetter fra
produktnavn. Syntetiske beta-ruter beholdes frem til en egen vurdert migrering.

[URL-LIVE-SAMPLE.json](URL-LIVE-SAMPLE.json) dokumenterer i tillegg fem direkte
HTTP-kontroller 23.10.2026: forside, betaoversikt, eksisterende Alligator-produkt,
Hjem og hage-kategori og betaens TV-guide. Alle svarte 200 med noindex; ingen
canonical-tag ble funnet i disse fem svarene. Observerte interne lenker er
lagret. Ingen kommersiell clickout ble besøkt. Dette er en begrenset live-prøve,
ikke full crawl eller historisk migreringsaudit. Authentisert canonical
produksjonskatalog, Search Console-eksport, CDN-logger, backlink-data og full
Wayback/.aspx-liste er ikke tilgjengelige i repoet. Profilens historiske eksempel
`/Shopping/Blomster/EuroFlorist.aspx` har ingen bevist etterfølger og får ingen
automatisk mapping. Manglende data er cutover-blokkere, ikke tillatelse til
å sende historiske URL-er til forsiden eller erklære dem alle permanent borte.

## Åpne avhengigheter og tester før cutover

1. **Varig og atomisk property route/alias registry:** Chillout må levere
   godkjent canonical identitet, publish eligibility, fryst slug, historiske
   reservasjoner, revisjon og kontrollerte livssyklusvedtak. Unik reservasjon
   må tåle samtidige publish-forsøk og retries. Lokale tester beviser parallelle
   *lesere* og avvisning av kolliderende snapshots, ikke atomisk allokering i
   en produksjonstjeneste. Ingen slik tjeneste er opprettet her.
2. **Representativ ekte katalog:** kollisjonssimulering må kjøres på godkjente
   canonical produkter/kategorier, med faktiske identitets-/variantdimensjoner.
   Daterte offentlige navn er ikke tilstrekkelig identitetsevidens. Syntetiske
   modell-/kapasitets- og livssyklustester er ikke dette produksjonsbeviset.
3. **Telefonfarger:** godkjent modell+lagring → canonical hovedside, eksplisitt
   farge-/variant-ID, riktig bilde, tilbud og prisgrunnlag per valgt farge.
   Dagens generelle tilbudssvar gir ikke en verifisert fargeseleksjonskontrakt.
   Ingen `?farge=`-velger eller sammenslåing av eksisterende produktidentiteter
   implementeres ved gjetning. TV-størrelse/kapasitet følger allerede separate
   canonical identiteter; representativ ekte variant-/ProductGroup-test gjenstår.
4. **Ekte HTTP-redirects:** nåværende GitHub Pages utfører ikke JSON-planen.
   En separat godkjent edge/hosting-adapter må implementere den, inkludert
   status, case/slash, query-bevaring og 404/410. Test faktiske HTTP-svar,
   ett hopp, mål-200 og canonical før cutover. Ingen adapter er aktivert.
5. **Brand/guide og livssyklusdata:** godkjente entiteter/innhold må kobles til
   samme registry før disse sidene inngår i normal produksjonsrendering.
6. **Historisk URL-audit og kontrollert aktivering:** kompletter datakildene
   over, vurder trafikkpåvirkning og test godkjente mål. Deretter separat
   review av routing, sitemap, schema, crawlbarhet, rollback og publisering.

## Verifisering

- 117 Python-tester består: 87 eksisterende og 30 ADR-039-tester.
- Nye tester dekker kollisjoner, suffix/ID-only, frysing, reservasjoner,
  korrigering/merge/fjerning, canonical-binding, separate kapasitetsidentiteter,
  kategoriaktivering, taksonomiflytting, interne lenker/ankere, søkeindeks,
  canonical, noindex, tomt sitemap og redirect-plan med bygde mål.
- Readiness testes med både `/` og `/preview/`, og lekkasjekontroll kjøres
  på generert output. Ingen plattform-ID når HTML eller søkeindeks.
- Eksisterende beta bygges/pakkes; offline lenke-/ressurskontroll og
  lekkasjekontroll kjøres. Ingen CSS eller godkjent design er endret.
- Ingen live HTTP-redirect-, ekte katalogkollisjons-, fargetilbuds-, atomisk
  allokerings- eller produksjons-ProductGroup-test påstås bestått.

Kun `sjekkpris-no` endres. Ingen merge, deploy, migrering, publisering,
Autodeploy-aktivering eller endring i `chillout-platform` er utført.

## Kritisk gjennomgang av PR #34 — 23.10.2026

Gjennomgangen fant følgende feil i den opprinnelige readiness-implementeringen;
de er rettet i samme gren og dekket av regresjonstester:

| Funn | Konsekvens før retting | Retting |
| --- | --- | --- |
| P1: Historiske kategoriadresser ble avledet fra dagens navn | Navnerettelse kunne opprette en ikke-verifisert migreringsregel og miste den ekte gamle adressen | Bare eksplisitte, dokumenterte kategori-aliaser brukes. Også dagens gamle produktadresser må finnes i registry før en plan godtas. |
| P1: Tidligere aliaser krevde at mål-ID fortsatt var aktiv | Ny merge av et tidligere mål stoppet ellers legitimt bygg, og gamle aliaser kunne ikke følge livssyklusen | Følg godkjente canonical etterfølgere og skriv direkte sluttmål; propagér dokumentert 404/410 uten redirect til borte-side. Avvis sykluser. |
| P1: Property og oppslagsalias i API-svar ble ikke kontrollert | Et feillevert svar med en annen registrert produkt-ID kunne bli bundet til feil offentlig adresse | Katalog og tilbud må ha riktig Property; namespace/local_slug i tilbudsidentiteten må samsvare når disse feltene leveres. |
| P2: Bare sluttmålets slash-variant var normalisert | Gammel directory-adresse uten slash kunne få en ekstra host-redirect før migreringsredirect | Begge gamle stavemåter har samme direkte sluttmål; motstridende regler avvises. |
| P2: Gammel redirect-plan overlevde mislykket retry | En eldre plan kunne forveksles med resultatet fra et nytt, mislykket bygg | Planen fjernes ved starten av et nytt bygg og skrives kun etter bestått validering. |
| P2: Snapshot-objekter kunne endres etter validering | Mutasjon av opprinnelig input endret rutene i en eksisterende resolver | Resolveren bruker sin egen dype kopi. |
| P2: Sitemap og lenkenes foretrukne stavemåte var ikke kontrollert fullt ut | Ikke-tomt/ugyldig sitemap eller lenke uten slash kunne passere porten | XML-validering krever tomt noindex-sitemap; interne innholdslenker må bruke canonical directory-sti. |

ADR-037 er i tillegg kontrollert med ett produkt som har både primærkategori
og tilleggskategori. Begge komplette leverte stier aktiveres; en tom registrert
gren publiseres ikke. Dette oppretter ingen konkurrerende kategoriinndeling.

**Produksjonsvurdering: fortsatt ikke klar for URL-overgang.** De seks åpne
avhengighetene over gjelder fortsatt. Et syntetisk rutesnapshot beviser verken
korrektheten i den ekte canonical katalogen, at publish eligibility er riktig,
at hele ancestor-grafen er levert, eller at historikken er komplett. Forrige
snapshot er fortsatt et eksplisitt lokalt input, ikke en atomisk beskyttet
produksjonshistorikk. Brand-/guide-URL-validering er ikke komplette sideadaptere;
og `?farge=` med korrekte tilbud/bilder, ekte ProductGroup-/variantvalidering,
indekserbart produksjonssitemap og operative HTTP-redirects gjenstår. Noindex
skal beholdes til en separat godkjent indekserings-/publiseringsvurdering.
