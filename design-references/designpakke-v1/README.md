# SjekkPris produktside – designprototype v1

12. oktober 2026. Visuell retning godkjent i chatten; denne HTML-implementasjonen er et nytt reviewgrunnlag, ikke godkjent produksjonskode. PR #1 skal ikke merges på grunnlag av denne leveransen alene.

Åpne SjekkPris-produktside.html i nettleseren. Filen fungerer uten installasjon og uten nettverk. Alle butikker, priser, leveringstider og lagerstatuser er eksempeldata. Produktillustrasjonen er AI-generert, ikke et autentisk produsentfoto.

## Arbeidsdeling
ChatGPT eier design og visuell gjennomgang. Claude integrerer godkjente komponenter med eksisterende kode og Chillout-kontrakter. Denne pakken endrer ikke repository, API, produksjon eller clickout.

## Visuell kontrakt
- Sans-serif, marine #10203b, primær grønn #006454, mint #edf8f4. Ingen fontlast fra eksterne tjenester. Arial/systemfallback i prototypen; endelig font må samsvare med den godkjente visuelle retningen. Mulish-vedtak for Kontaktlinser er ikke automatisk et SjekkPris-vedtak.
- Maks container 1224 px. Desktop fra 1000 px: produktbilde / produktinformasjon / prisområde i 1.05fr 1fr 1fr. Dette er et konkret implementasjonsvalg som må vurderes visuelt, ikke en påstand om identiske proporsjoner med originalen.
- Mobil: header/søk → breadcrumb → produktnavn → bilde → variant → attributter → prisområde → tilbud. 16 px sidemarger. Klikkflater minst 44 px. Tilbudsradene skifter fra tabell-lignende desktop-layout til stablede mobilkort.
- Alle CTA-er: «Gå til butikken». Butikknavnet står separat. Norske priser: 14 990 kr.
- Prisgrunnlag: laveste kjente totalpris blant tilbud med kjent frakt. Ukjent frakt er nullverdi, aldri null kroner. Ved manglende kjent frakt: laveste varepris + «Frakt ukjent». Null tilbud gir tomtilstand uten CTA.
- Høyre prisområde viser varepris + frakt. Opplysninger om ukjent frakt gjelder hele sammenligningen og skilles fra vinnerens frakt.
- Ingen oppdiktede anmeldelser, rabattsignaler eller historisk graf. Prishistorikk har en eksplisitt tomtilstand.

## Interaksjoner
Demolinjen over nettstedet bytter datasett (kjent totalpris / all frakt ukjent / ingen tilbud). Søk viser bare ett lokalt demoprodukt eller en hjelpsom tomtilstand. Meny og seksjonsankre fungerer. FAQ bruker native details. Butikk-knapper viser en dialog og sender ingen trafikk. Variantene utover 65 tommer er inaktive til reelle variantlenker foreligger. Ikke publiser demolinjen eller demodialogen i produksjon.

## Claude-overlevering
1. Behold brukbar dataintegrasjon fra eksisterende PR. Flytt HTML-struktur, CSS-tokens og responsive regler til eksisterende komponenter uten å redesigne.
2. Erstatt eksempeldata og illustrasjon med kontraktverifiserte produkt-/tilbudsdata og rettighetsavklarte produktbilder. Modelltekst og egenskaper her er designinnhold fra originalreferansen og må verifiseres mot katalogen.
3. Bruk eksisterende clickout-kontrakt; ikke bygg en ny. Ikke vis demo-dialogen i produksjon.
4. Implementer autocomplete, reelle variantlenker og reell prishistorikk når data finnes. Behold korrekte tomtilstander ellers.
5. Lever faktiske skjermbilder på 360, 390, 430 og 1280 px samt kjent totalpris, ukjent frakt og null tilbud. Kontroller overskriftsrekkefølge, overflyt, lang tekst, tab/fokus og at alle knapper har fungerende handling.
6. ChatGPT/brukeren gjennomgår skjermbilder før merge. Ikke rapporter «ingen avvik» uten visuell sammenligning mot godkjente referanser.

## Verifikasjonsgrense
Denne leveransen er ikke skjermbildekontrollert i nettleser: tilgjengelig miljø mangler støttet browser-QA. Kildekode/syntaks og prisberegning er kontrollert separat. Det er derfor ikke dokumentert pikselfidelitet, faktisk fontgjengivelse eller fravær av layout-overflyt. Ingen påstand om 95 prosent fidelity.
