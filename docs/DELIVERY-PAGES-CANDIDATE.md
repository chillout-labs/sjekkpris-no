# Complete qualified catalogue via existing Pages — Draft integration

Owner clarification 30 October 2026: use normal catalogue publication, not a
Toalson patch. A complete rebuild is acceptable when existing identities, routes,
design and functionality are preserved. New qualified products belong in product
pages, category listings and search; public product/category pages may be indexed
only after a separately approved release. No public change accompanies this PR.

## Responsibility and actual implementation

Chillout #292/#300 still owns qualification, current Core/URL/Delivery authority,
source facts, private rendering and audited receipts. Existing consumer #37 and
original #231 receiver stay pinned, not copied or merged here. Other Commerce
Properties reuse Core's receiver/inventory/diff; their own templates, domains,
routes and publication decisions stay with their website repository.

This repository owns `tools/delivery_candidate.py`: inspect the complete received
site, require every product in internal search and at least one category listing,
check image presence, existing affiliate link shape/rel, reject conflicting
canonicals, and apply explicit candidate SEO. It does NOT classify products,
compute prices, create identities, render a replacement design or fetch feeds.
Actual image rights/bytes and price/availability remain upstream qualification
gates; this inspection does not prove them from an img tag or amount string.

`tools/review_delivery.py` calls the pinned Core utility, which invokes original
#231 `receive`, then checks the website and compares complete file inventories.
Missing files refuse unless covered by the exact reviewed test-catalogue retirement
plan below. Changed non-catalogue content, CSS/JS, assets or beta refuses.
Shared homepage/search/category content changes are reported in the full diff,
not silently accepted as publication authority. Review this diff for expected
new membership and unrelated product changes before release. Core hash verification
does not prove live revocation checks or ownership of a public URL.

No renderer reruns after receipt. Existing qualified renderer already produces
product, search and category surfaces from one input. It must be supplied the
FULL qualified catalogue: a one-product private build is not a replacement for
a real qualified catalogue. The original design-test catalogue may be retired
as explicitly approved below. Withheld products must never be silently republished
to satisfy a preservation check; withdrawals need a separately reviewed release.

## Candidate path in the existing workflow

The ordinary Pages workflow is not replaced. A nonempty `delivery_run_id` takes
the new review-only branch and suppresses ordinary build/deploy. Empty input keeps
existing behavior, so do not dispatch an empty-input run for candidate testing.
The review branch has only read permissions, no Pages environment and no deploy
or artifact-upload step. Inputs are validated and passed through environment
variables, never interpolated as shell code. Receiver and Core checkout refs are
exact commits. The original receiver implementation is additionally SHA-256 pinned.

The input artifact is named `delivery-input`, in an existing completed run in
THIS repository, and contains `bundle.tar` and `baseline.json`. Independent
result/baseline hashes must come from reviewed evidence, not a URL or the archive's
own claims. Public SjekkPris Actions accepts **synthetic evidence only** here.
Real private packages and receipts must not be uploaded to this public repository
as a transfer workaround. Real local review can use the same CLI in the existing
private execution context without `--synthetic-only`.

Chillout is private, SjekkPris public. The default repository token cannot read
private Core. The checkout explicitly supports an existing, approved read-only
`CORE_REPOSITORY_READ_TOKEN`; none was created, installed, read or granted by this
PR. Without authorized existing access the candidate job fails closed at checkout.
This is a real operational blocker, not proof of a successful cross-repo run.
Do not create a broad PAT or add write scopes to make it pass. The local composed
check uses already-authorized local checkouts and needs no new credential.

This slice deliberately does not wire real Railway-to-public-Actions transport
or turn a test grant into public permission. Selection of approved transport,
current-authority recheck, publication receipt and served release proof remains
the explicit #231/ADR-038 boundary. Do not remove `--synthetic-only` as a shortcut.
An eventual authorized publisher should use the existing upload/deploy steps on
the exact accepted complete tree, not fetch the live API again.

## SEO and URL rules

Default preparation preserves noindex and an empty sitemap. The explicit
`--indexable-candidate` option changes only qualified product and nonempty category
pages to `index,follow`, supplies an absolute self-canonical and writes the same
routes into `sitemap.xml`. Search, beta and other non-catalogue HTML stay noindex.
This flag creates an offline review artifact, not permission to publish/index.
Existing `ROBOTS_NOINDEX` or runtime variables are not changed by the candidate job.

Relative private `/go/tgt_…` anchors are normalized to the exact existing public
`https://sjekkpris.no/go/tgt_…` form, without changing the target or ranking decision.
The existing output leak check remains mandatory. Its only additional exception
is the literal crawler directive `Disallow: /go/` in `robots.txt`; no token, URL
or other file is exempted. Provider destinations are never derived here.

Existing `/p/{namespace}/{slug}/` and newer Core `/p/{slug}/` paths are preserved
as supplied; the receiver never automatically migrates one to the other. A full
candidate that loses old routes outside the explicit test-catalogue exception is
refused. General route ownership/aliases remain governed by the existing registry. Core's private renderer currently also
uses `/sok/` and `/k/`; old `/search/` and `/kategori/` must not disappear unnoticed.

No CSS/layout/template or price/ranking formula changes. Head metadata, exact
clickout prefix and removal of the known private readiness decoration in an
explicit public candidate are the only HTML rewrites. Mobile/design/browser acceptance on
the final REAL complete candidate remains required; synthetic parsing does not
claim visual fidelity, actual clickout resolution or an indexed Google result.

## First baseline and first complete Toalson delivery

The last successful deployment is 7313878648 / run40198535501 / source08892adf,
25 October. Its original Actions artifact is no longer listed. Later green
run40929641304 skipped build/deploy. Obtain an existing retained complete archive
first. If unavailable, review the deployed generator/packager's COMPLETE finite
output list, collect served bytes for every listed path with release drift checks,
and independently accept that completeness. A crawl or current live API rebuild
alone cannot establish historical completeness. Never invent missing old files.

The companion Core work order describes the inventory format and recovery limits.
If complete reconstruction cannot be proved, a separately reviewed first full
baseline is required. This PR does not assert that this has happened. Future
accepted releases need retained full archives/inventories tied to deployment IDs,
not only short-lived Pages artifacts; no storage/retention settings change here.

Remaining first-delivery gates: full baseline; full qualified input plus explicit test-catalogue retirement, preserving design/other pages/beta; actual limited SQL-role acceptance and fresh short owner grants;
private transport and public boundary authority; exact full diff; mobile/desktop,
canonical/noindex-or-approved-indexing, sitemap, images/prices/affiliate QA. Toalson
is first test data for that SAME flow, not a branch or hardcoded ID in this code.
Wait to sign in until those dependencies are ready, because owner evidence expires.

## Evidence, release and rollback

Eight targeted website tests cover default/private and explicit indexed candidates,
search/category coverage, existing namespace URLs, conflicting canonicals, unsafe
clickouts, reused leak protection, removed routes and changed design. Original
documentation guard tests are reused. Local synthetic composition used original
#231 receiver plus companion Core tool and this CLI in both SEO modes successfully.
No real package, source credential, build, SQL mutation or publication was used.

Keep original private result/tree hash separate from the website SEO-projected
candidate hash and all before/after file descriptors. A hash authenticates bytes
only against a trusted expected hash. It does not authenticate the operator or
renew a revoked grant. Retain receipts outside the public site.

Before any future release recheck authority/source/target and current deployment,
serialize with the existing Pages concurrency group and bind upload to reviewed
candidate hash. After release verify actual served identity and URLs. Rollback
republishes the retained prior complete artifact; no database restore, URL history
deletion or blind retry after unknown outcome. Merging this workflow/code PR can
trigger the existing ordinary operational push path: **do not merge without a
separately approved rollout decision**. No merge/deploy was performed here.

Learning: full rebuild is the normal scalable approach, but historical preservation,
data authority, candidate verification and public release proof are distinct.
Keep this in the existing Delivery/Pages history; no parallel engine or learning
registry, and no AI promotion of a new platform policy.


## Approved review corrections and Pages handoff — 30 October 2026

VEDTATT: The owner identifies the original 16 products as design-test content.
They may be removed/replaced by the first real qualified catalogue, including
slugs and URL history, without 301s. This supersedes earlier preservation/migration
requirements in this document **only for that catalogue**. Other pages, design and
functionality remain protected; Core URL rules for real products are unchanged.
No real product is selected, approved or published by these code changes.

IMPLEMENTERT in #41:

- Only categories linking to products in the received catalogue join the indexable
  set. Empty categories remain noindex and are excluded from sitemap.
- The exact existing private readiness banner is removed from the staging copy
  only for explicit indexable candidates. Private mode retains it. Unknown private
  decoration refuses rather than being stripped by a broad text/HTML rule.
- All HTML anchor destinations on this host (absolute or relative, including
  preserved pages) must resolve inside the candidate. Dynamic /go/ continues to use
  its existing resolver contract. Search membership must exactly equal product pages;
  categories cannot link to missing products; sitemap is regenerated from eligible
  received routes. No website taxonomy/ranking/identity decisions are invented.
- Optional `--retirement PLAN --retirement-sha256 INDEPENDENT_HASH` accepts a reviewed
  list, not a general deletion switch. PLAN has version
  `sjekkpris.test-catalogue-retirement.v1`, `scope: ["sjekkpris-no", "test"]`,
  `baseline_tree_sha256`, and `files` containing the original exact path/bytes/sha256
  descriptors of the test product index.html files. Every descriptor must match the
  hash-verified baseline. Only product HTML paths are eligible; duplicate entries,
  changed scope/baseline, retained retired products or any unlisted deletion refuse.
  The independently accepted plan hash remains in the private review report.
  Build the replacement catalogue upstream; this verifier never deletes products.
  No actual retirement plan is fabricated from the incomplete live observation.

The workflow accepts optional `retirement_sha256` with retirement.json in the
SYNTHETIC input. `candidate_tree_sha256` optionally stages the result into `_site`
using #304, the same path consumed by existing upload-pages-artifact. Supply this
hash from the separately reviewed FINAL candidate report, then reproduce/verify
that exact result. CLI equivalents: `--pages-site NEW_DIRECTORY
--candidate-tree-sha256 REVIEWED_FINAL_HASH`. A mismatching or absent paired hash
refuses. No API build, feed read or renderer runs between review and staging.
All candidate-related inputs suppress the ordinary build path, including incomplete
input combinations; they cannot accidentally fall through to a normal publication.

The candidate branch still has no upload/deploy step and accepts synthetic inputs
only in public Actions. Real local use remains in the existing private context.
This prepares the file handoff to existing Pages; it does not claim the real private
transfer/current-authority boundary is implemented or verified. After a separate
release decision, existing upload/deploy must consume only this exact accepted tree,
with fresh authority/source/target/baseline checks and audit. Do not enable a boolean
publish input as a substitute, expose private receipts, or grant a new token.

Evidence: 14 targeted website tests pass, including all three corrections,
retirement tampering and preserved-page broken links. Existing 15 workflow guard
tests pass. Local composition using original receiver and companion Core stages
both SEO modes successfully and refuses a wrong final tree hash. YAML and candidate
permission/deploy isolation inspected. No full suite manually repeated. Mobile,
actual structured data, current price/image/clickout and live release acceptance
still require the first REAL candidate; no screenshot or public URL proof is claimed.

Learning: content coverage, indexability and release authority are separate. A
private renderer's decoration is not public presentation merely because robots
changes. The scoped retirement and final-tree hash tests now prevent these specific
regressions. Follow-up stays in #41/#304, not a parallel engine or new learning
register. No AI-authored policy promoted; no merge/deploy/publication performed.

Companion Core pin for staging: `e0cadebd2b1ebde941969ded3da7f7323250e568`
(#304). Original receiver pin and implementation hash are unchanged.
