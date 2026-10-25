"""Consent-aware, nonblocking analytics events. No raw clickout tokens are exported."""
def events_markup() -> str:
    return r'''<script>
(function () {
  "use strict";
  function consented() {
    try { return localStorage.getItem("sp-analytics-consent-v1") === "accepted"; }
    catch (_) { return false; }
  }
  function track(event, fields) {
    if (!consented()) return;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({event:event},fields||{}));
  }
  function productPath(url) {
    try {
      const u = new URL(url, location.href);
      if (u.origin !== location.origin) return null;
      const match = u.pathname.match(/\/p\/([^/]+)\/([^/]+)\/?$/);
      return match ? {product_namespace:match[1], product_slug:match[2]} : null;
    } catch (_) { return null; }
  }
  const current = productPath(location.href);
  if (current) {
    track("view_item",Object.assign({item_name:
      document.getElementById("product-title")?.textContent?.trim() || ""},current));
  }
  document.addEventListener("submit",function(e) {
    const form = e.target;
    if (!(form instanceof HTMLFormElement) || !form.matches(
      "#home-search-form, #search-form-results")) return;
    const input = form.querySelector('input[name="q"], #search-input-results');
    const term = input?.value?.trim() || "";
    if (term) track("search",{search_term:term.slice(0,100)});
  }, true);
  document.addEventListener("click",function(e) {
    const target = e.target instanceof Element ? e.target : null;
    if (!target) return;
    const shop = target.closest('a.sp-cta[href]');
    if (shop) {
      try {
        const url = new URL(shop.href,location.href);
        // Never send the token, click ID, provider URL or full clickout URL to GA4.
        if (url.origin===location.origin &&
            /^\/go\/tgt_[0-9A-HJKMNP-TV-Z]{26}$/.test(url.pathname)) {
          const merchant = (shop.getAttribute("aria-label") || "")
            .replace(/^Gå til butikken:\s*/,"").slice(0,100);
          track("merchant_click",Object.assign({merchant_name:merchant},current||{}));
        }
      } catch (_) {}
      return;
    }
    const card = target.closest('.sp-product-card a[href]');
    if (card) {
      const item=productPath(card.href);
      if (item) track("select_item",Object.assign({
        item_name:card.querySelector("h3")?.textContent?.trim() || "",
        item_list_name:document.querySelector(".sp-listing") ? "catalogue" : "homepage"
      },item));
    }
  },true);
})();
</script>'''
