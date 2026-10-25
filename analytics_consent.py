"""Consent-gated GTM integration for public SjekkPris HTML pages.

GTM is loaded only after explicit analytics opt-in. This is basic consent mode
(no Google requests at all before consent), not advanced Consent Mode v2.
"""
GTM_ID = "GTM-MV3B5Z87"

def head_markup() -> str:
    return """<style>
#sp-consent{position:fixed;bottom:16px;left:16px;right:16px;max-width:550px;margin:auto;padding:18px;background:#fff;color:#10203b;border:1px solid #cbd5e1;border-radius:12px;box-shadow:0 8px 32px #10203b30;z-index:99999;font:15px/1.5 system-ui,sans-serif}
#sp-consent[hidden]{display:none}
#sp-consent p{margin:0 0 12px}
#sp-consent .sp-consent-actions{display:flex;flex-wrap:wrap;gap:8px}
#sp-consent button,.sp-consent-settings{cursor:pointer;border:1px solid #006454;border-radius:8px;padding:9px 13px;font:inherit;background:#fff;color:#006454}
#sp-consent button[data-choice="accept"]{background:#006454;color:white}
.sp-consent-settings{background:transparent;border:0;text-decoration:underline;padding:0;color:inherit}
</style>"""

def body_markup() -> str:
    return f"""<div id="sp-consent" role="dialog" aria-label="Valg av informasjonskapsler" aria-modal="false" hidden>
<p><strong>Analyse og informasjonskapsler</strong></p>
<p>Vi bruker valgfri Google Analytics for å forstå hvordan SjekkPris brukes. Vi laster ikke Google Tag Manager før du samtykker. Du kan endre valget når som helst.</p>
<div class="sp-consent-actions">
<button type="button" data-choice="reject">Avvis analyse</button>
<button type="button" data-choice="accept">Godta analyse</button>
</div></div>
<script>
(function(){{
  "use strict";
  var key="sp-analytics-consent-v1", choice=null, loaded=false;
  try {{choice=localStorage.getItem(key);}} catch(e) {{}}
  var dialog=document.getElementById("sp-consent");
  function loadGtm(){{
    if(loaded) return;
    loaded=true;
    window.dataLayer=window.dataLayer||[];
    window.dataLayer.push({{"gtm.start":Date.now(),event:"gtm.js"}});
    var s=document.createElement("script");
    s.async=true;
    s.src="https://www.googletagmanager.com/gtm.js?id={GTM_ID}";
    document.head.appendChild(s);
  }}
  function update(v){{
    choice=v;
    try{{localStorage.setItem(key,v);}}catch(e){{}}
    dialog.hidden=true;
    if(v==="accepted"){loadGtm();document.dispatchEvent(new Event("sp-analytics-enabled"));}
    else if(loaded)window.location.reload();
  }}
  dialog.querySelector('[data-choice="accept"]').addEventListener("click",function(){{update("accepted");}});
  dialog.querySelector('[data-choice="reject"]').addEventListener("click",function(){{update("rejected");}});
  document.querySelectorAll(".sp-consent-settings").forEach(function(b){{b.addEventListener("click",function(){{dialog.hidden=false;}});}});
  if(choice==="accepted")loadGtm();
  else if(choice!=="rejected")dialog.hidden=false;
}})();
</script>"""

def footer_link() -> str:
    return '<button type="button" class="sp-consent-settings">Innstillinger for analyse</button>'
