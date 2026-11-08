# Incremental HTML receiver — inactive development slice

2026-11-08. Owner authorized isolated implementation and Draft PR only. Existing
#41/#42/#43 and Pages release/approval checks are unchanged. No deployment config,
bucket, route, credentials, migration or publication is supplied by this draft.

## Implemented

- `tools/render_delivery_html.py`: callable paired rendering using existing
  `build.product_body/page`, CSS, unknown-price/shipping semantics and clickout
  helper. Both variants preserve explicit route/canonical/noindex. Active offers
  and Product/Offer JSON-LD use the same immutable comparison. Fallback renders
  empty offers and no Offer JSON-LD or purchase link; no edge HTML manipulation.
- `edge/worker.mjs`: read-only GET/HEAD receiver. Fixed deployment scope and
  public origin, SHA-256 checked immutable content/cache, short status lease,
  minimum revision, revocation and fail-closed selection. No admin/test/write
  endpoint, price computation, ranking, matching, qualification or network feed.
- Immutable HTML may be cached; complete HTTP responses use `no-store` so a
  warm full-page cache cannot skip the current validity check. Control is read
  again before returning. Failed/missing active HTML falls back; failed fallback
  returns 503. Unknown/missing/corrupt/expired status never enables offers.
- The existing output leak gate is reused per generated HTML object.
- Isolated local runtime CI; no deploy job or external credential.

## Interoperability contract

`<scope>/html-v1/current`: `contract="chillout.html.v1"`, `scope`, increasing
`sequence`, maps `pages` and `status` from two-hex route hash to object SHA-256.
Scope is SHA-256(compact UTF-8 JSON `[property_id, environment]`), never inferred
from hostname. Immutable content is `<scope>/html-v1/objects/<sha256>`.

Page shard: exact `/p/<frozen-slug>/` -> `{id, revision, valid_until, html, fallback}`.
Status shard: exact route -> `{min_revision, revoked, issued_at, valid_until}`.
Seconds since epoch; integer revisions; explicit boolean revocation. Maximum
lease 300 seconds and object size 2 MiB. URL-bound records and complete HTML
come from the existing authorized Delivery producer. No arbitrary remote URL
is fetched. No mutable control/status response is cached independently.

Required future bindings: `HTML` (private R2 read binding), `DELIVERY_SCOPE`,
`PUBLIC_ORIGIN`. No wrangler/deploy manifest is added. The receiving Worker has
no storage write code. Other website paths stay on the existing origin through
future explicitly scoped routes; this Worker must not replace the entire site.

## Verification and limits

- Existing 133 Python tests pass (including 4 paired-rendering regressions).
  Category, search, composition, sitemap/SEO and Pages tests remain intact.
- 11 Node receiver tests pass. Actual local workerd/R2 test also passes for
  response delivery, warm-cache revocation and competing conditional writes.
- Desktop and 390px iframe viewport manually checked in the supported browser
  with synthetic fixture pages. Existing layout and mobile sections render;
  fallback has no buy action. This is not a pixel-diff baseline, real device test
  or regression of every future real product/image. Fixture uses a missing image.
- Existing style hash/assets, navigation aliases, sitemap and price-bearing search
  index are NOT automatically republished by this receiver. Exact current-site
  asset/URL composition is a pre-activation requirement, not a completed check.
- Search/category commercial fields remain unchanged in today's Pages pipeline.
  Before cutover, the qualified consumer must emit price/stock-free discovery
  cards/index and omit obsolete price filters, or deliver consistent current
  commercial revisions. This draft does not claim discovery prices are now live.
- It remains necessary to bind the producer to its existing durable order/audit
  lifecycle, current Core grants and authoritative status projection, with an
  isolated DB integration test. No production access or new grants were used.

Run `python -m unittest discover -s tests -q`; then `cd edge && npm ci
--ignore-scripts --no-audit --no-fund && npm test`. Fixtures never click affiliates.

## Next approval

Review the drafts and outstanding integration points first. Only then approve a
private Cloudflare test with explicit nonproduction bucket/host, credential scope,
budget and cleanup. Test real S3 conditional writes and timeouts, source revocation,
status lease outage and the read-only Worker. A later production decision remains
separate. 10k local synthetic adapter records are not Cloudflare capacity evidence;
100k/1m require request-amplification and shard-size measurement.
