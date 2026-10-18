# SjekkPris – Butikksider v1

Status: Besluttet av bruker 18. oktober 2026. Dette er gjeldende retning for
butikkmalen og erstatter tidligere forslag om «Vis alle» og erfaringer i denne
arbeidsrunden. Endringer i retningen avtales særskilt.

## Innhold og rekkefølge

1. Logo, butikknavn, kort nøktern beskrivelse og dokumenterte nøkkeltall.
2. Produkter og priser, med søk innenfor butikken, kategorier og sortering.
3. Utvalg og eventuell dokumentert pris-/klikkinnsikt.
4. Om butikken og «Dette bør du vite før du handler»: frakt, levering, retur,
   garanti og kundeservice med kilde, gyldighetsområde og kontrolldato.
5. Kilder, redaksjonelt ansvar og dato for oppdatering.

Snarveier øverst gjør butikkopplysningene tilgjengelige uten å bla gjennom
produktlisten. Samme mal brukes for små og store butikker; manglende data skal
ikke erstattes med påstander eller konstruert statistikk.

## Produktvisning og store kataloger

- Standard: 12 produkter per side på både mobil og desktop.
- Ingen «Vis alle» eller ubegrenset akkumulering av produktkort.
- Forrige/neste, sidetall og «Viser 13–24 av …» gir oversikt.
- Søk og filtre gjelder hele butikkens tilgjengelige utvalg hos SjekkPris,
  ikke bare den viste siden. Endring av søk/filter/sortering starter på side 1.
- Nøytral navnesortering som standard. Pris sorteres med stabil sekundærnøkkel.
- Butikkopplysninger følger etter ett begrenset produktutvalg, ikke etter hele
  katalogen. Ved sidebytte flyttes fokus til produktoverskriften.
- Tomme treff kan nullstilles. Lastingsfeil skal ha mulighet for nytt forsøk.
- Produktantallet gjelder unike sammenligningsprodukter med aktive tilbud fra
  butikken hos SjekkPris. Varianter med egen produktidentitet telles separat.
  Det er ikke butikkens fulle sortiment og ikke antallet rå feedrader.

### Krav til produksjonsintegrasjon med Chillout

Søk, filter, sortering, antall og sideutvalg må beregnes hos serveren eller i
publiseringslaget. Nettleseren mottar maksimalt én side med produktdata per
forespørsel, ikke et komplett søkeindeks-/produktdatasett for 100 000 produkter.
Fast øvre sidegrense, stabil rekkefølge og konsistent snapshot må ivaretas.
Kategori-/merkelister må også ha begrenset størrelse eller søk ved store utvalg.
Side-/søketilstand skal kunne deles og gjenopprettes med tilbakeknappen.
Betaen demonstrerer dette med q, gruppe, sort og side i URL-en.
Indeksering av sidevalg og filterkombinasjoner avklares i eksisterende SEO-spor;
vi oppretter ikke automatisk indeksérbare butikk × kategori × filter-sider.

### Hva betaen faktisk demonstrerer

Baby Brezza-forslaget bruker 15 daterte, offentlige produktoppføringer fra
18.10.2026. Første HTML viser 12 kort. Flere kort hentes bare ved behov, og
produktlisten inneholder aldri mer enn 12 kort samtidig. Et lite søkeindeks
med de 15 eksempelproduktenes navn, grupper og priser brukes lokalt i betaen.
Dette er en designfixture, IKKE produksjonsadapteren for store kataloger.
Den må ikke utvides ved å legge hele store butikkataloger i nettleseren.

## Fakta og statistikk

- Produkter og priser kommer først. Prisgrunnlag og tidspunkt skal fremgå.
- Ukjent frakt er ikke gratis frakt. Butikkvilkår må gjelde riktig produktgruppe.
- Popularitet betyr dokumenterte videreklikk fra SjekkPris, med oppgitt periode,
  tilstrekkelig grunnlag og filtrering av intern-/bottrafikk. Ikke «bestselgere».
- Ingen egen billigst-score basert på produkter uten reelle sammenlignbare tilbud.
- Ingen innhentede anmeldelser, stjerner eller TrustScore uten avklarte rettigheter.

## Affiliate og kilder

Alle aktive lenker til butikkens nettsted skal bruke godkjent affiliate-sporing
for den konkrete destinasjonen, også frakt, garanti, kontakt og kildesider hos
butikken. Bruk eksisterende godkjente SjekkPris-clickout, synlig annonselenke-
merking og rel="sponsored nofollow". Ingen konstruerte tokens, direkte fallback,
eller gjenbruk av en produktlenke til en annen destinasjon.

Når riktig lenke mangler, er handlingen inaktiv i betaen. Butikkens kildedomene
kan oppgis som ren tekst. Interne produktlenker er vanlige interne lenker.
Eksterne uavhengige kilder er ordinære kildelenker; eventuelle anmeldelseskilder
har en sekundær plass. Nye faner må varsles. Disse lenkene gir ikke rett til å
republisere innholdet. Klikk på frakt/kontakt må skilles fra produktklikk i statistikk.

## Erfaringer – eget senere segment

Brukeren utsatte 18.10.2026 hele funksjonen for innsending av erfaringer.
Den skal senere vurderes samlet for både butikker og produkter, med separate
vurderingsgrunnlag og eventuell felles innlogging/moderering. Ingen skjemaer,
stjerner, poengsummer eller innsamling av personopplysninger bygges nå.
Dokumenterte butikkfakta skal ikke fremstilles som egne kjøpserfaringer.

## Redaksjonelt ansvar og avgrensning

SjekkPris og Chillout forvalter opplysningene nå. Annonsørredigering og eventuell
selvbetjening er senere arbeid, med kildehistorikk og redaksjonell kontroll.
Betaen beholder noindex. Eksisterende produktidentiteter, URL-er, tilbudsrangering
og Chillout-kontrakter endres ikke av denne designbeslutningen.
