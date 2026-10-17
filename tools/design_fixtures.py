"""Explicit example-only display fixtures. Never imported by production build."""
from html import escape
from rich_ui import product_rail
from home_ui import render_product_card


def product_presentation(product):
    slug=product['local_slug']
    if slug=='demo-tv-6':return {}
    size=product['local_name'].split(' tommer')[0].split()[-1]
    panel='OLED' if 'OLED' in product['local_name'] else 'LED'
    return {
        'summary':'Denne eksempelmodellen kombinerer et slankt TV-design med et tydelig bilde. Opplysningene demonstrerer produktmalen og er ikke produsentfakta.',
        'attributes':[('Panel',panel),('Oppløsning','4K'),('Frekvens','120 Hz')],
        'variants':[(label,f'/p/catalogue/demo-tv-{i}/',slug==f'demo-tv-{i}') for i,label in [(1,'55 tommer'),(2,'65 tommer'),(5,'77 tommer')]],
        'gallery':[({'url':'https://sjekkpris.no/assets/tv-illustration.webp'},'Produktillustrasjon'),({'url':'https://sjekkpris.no/assets/tv-detail.webp'},'Detalj av samme illustrasjon')],
        'about':f'Designeksempel: {product["local_name"]} er en fiktiv {size}-tommers TV med {panel}-panel. Her prøver vi hvordan en fyldigere produktbeskrivelse, egenskaper og praktiske vurderinger fungerer sammen. Modellen er ikke et virkelig produkt, og opplysningene skal ikke brukes som kjøpsråd.',
        'specs':[('Skjermteknologi',panel),('Skjermstørrelse',size+' tommer'),('Oppløsning','3840 × 2160'),('Oppdateringsfrekvens','120 Hz'),('Tilkoblinger','4 HDMI-innganger')],
        'history':[('1. sep.',16990),('10. sep.',15990),('20. sep.',16490),('1. okt.',15490),('10. okt.',14990)],
        'use_cases':[('Film og serier','Eksempel: kontrast og detaljgjengivelse i mørke scener.'),('Gaming','Eksempel: høy oppdateringsfrekvens og støttede spillfunksjoner.'),('Streaming','Eksempel: apper og tjenester som faktisk støttes.')],
        'alternatives':[('Vil du bruke mindre?','Eksempel: mindre skjerm, med lavere varepris.','Se 55-tommersmodellen','/p/catalogue/demo-tv-1/'),('For omtrent samme pris','Eksempel: vurder annen paneltype og dine viktigste egenskaper.','Se alternativ modell','/p/catalogue/demo-tv-4/'),('Vil du gå opp?','Eksempel: større skjerm krever mer plass og høyere budsjett.','Se 77-tommersmodellen','/p/catalogue/demo-tv-5/')],
        'accessories':[('Veggmontering','Kompatibilitet må bekreftes mot festemål og vekt før et tilbehør vises som passende. Dette er en forklaring i designforhåndsvisningen.','Les eksempelguiden','/guide/velg-tv/')],
        'faq':[('Hva betyr 120 Hz?','Eksempelsvar: Skjermen kan oppdatere bildet opptil 120 ganger per sekund. Støtte avhenger også av signalkilden.'),('Er frakt inkludert i prisen?','Varepris vises som standard. Velg «Inkluder frakt» for kjent totalpris. Ukjent frakt blir aldri behandlet som gratis.')]
    }


def homepage_sections(products,*,base,money,day,segment):
    cards=[render_product_card(p,base=base,money=money,day=day,segment=segment) for p in products]
    return (product_rail('Dagens beste priser',cards[:4],'/kategori/tv/')+
            product_rail('Fortsett der du slapp',cards[1:3],'/kategori/tv/')+
            product_rail('Mest søkt akkurat nå',cards[2:6],'/kategori/tv/')+
            '<section class="sp-discovery"><div class="sp-catalogue-heading"><h2>Nytt og aktuelt</h2></div><div class="sp-editorial"><a href="/guide/velg-tv/"><h3>Slik velger du TV</h3><p>Eksempel på guidekort og redaksjonelt innhold.</p></a><a href="/kategori/tv/"><h3>Finn riktig skjermstørrelse</h3><p>Utforsk eksempelmodeller i flere størrelser.</p></a></div></section>')
