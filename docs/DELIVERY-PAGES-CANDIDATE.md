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

## 2026-10-30 — bounded catalogue composition and remaining beta conflict

VEDTATT: owner permits up to USD 5 additional necessary CI for #304/#41 and
catalogue composition in this Draft, retaining the reconstructed served beta.
No merge, deploy, rights, product approval or publication is authorized.

IMPLEMENTERT: `review_delivery.py` now requires `--baseline-site DIRECTORY` in
addition to the independently hashed inventory. #304 verifies every baseline file
and receives the bundle with the original receiver. `compose_catalogue.py` selects
received catalogue surfaces into a separate temporary candidate; it never renders,
fetches, changes identities, qualifies products or supplies authority. Received
beta is discarded; baseline beta, informational pages and existing assets remain
byte-identical. Conflicting protected assets referenced by new pages refuse.
The original receiver receipt and received hash remain distinct from the final
composed hash. Only a fully checked candidate is moved to the requested new path.

Existing `/search/` serves the received search page. Existing `/kategori/` routes
serve the received category navigation, remain noindex and outside sitemap; they
do not retain test-product listings or invent taxonomy. All anchors still must
resolve. Missing real product/category paths refuse unless explicitly covered by
the existing reviewed test-product retirement contract. No Toalson-specific code.
The same composition supports subsequent product groups without a retirement plan.
The public Actions artifact now additionally needs SYNTHETIC `baseline-site/`.
Private real input, receipts and baseline artifacts must not be uploaded there.
The exact Core pin and disconnected Pages publication boundary remain unchanged.

OBSERVERT: local tests: 14 existing candidate tests, 8 composition regressions,
15 workflow guard tests pass. Synthetic original-receiver -> composition -> exact
Pages-directory staging succeeds in private and indexable-candidate modes; a wrong
final hash refuses. No full suite repeated locally. The first local test attempt
could not write Windows temporary directories; rerun with normal temporary-file
access passed. No external service changed.

The actual reconstructed 128-file baseline exposes a REAL BLOCKER: the preserved
`beta/butikker/babybrezza/index.html` contains 24 anchors to 12 of the 16 retired
product routes. Strict removal plus byte-identical beta therefore cannot satisfy
internal-link integrity. The real-baseline synthetic candidate is correctly
REFUSED before a final candidate/staged output exists. The regression covers this
conflict; it is not waived. The 46 differing beta files must not be overwritten
with the private renderer's beta. No claim of a complete real candidate, mobile
QA, fresh Toalson data or public release is made.

FORSLAG/ÅPENT — owner decision: permit a narrowly reviewed link-only change to the
one affected beta page (preserving design/content), or keep referenced test pages
outside the real catalogue under a separately reviewed nonindexable retention
contract. Recommend the former: point retired catalogue links to the received
category navigation without inventing category membership. Neither option is
implemented/authorized by this slice. Until resolved, first complete delivery
remains blocked; do not weaken the preservation or link checks.

Learning check: complete file recovery does not prove that preserved navigation
is independent of retired catalogue content. Preserve actual bytes, then validate
cross-surface links before staging. This prevention is reusable by other Properties;
route mapping and the test-catalogue exception belong only to SjekkPris. The
observed cause and regression live here and in #41/#304, without a new register
or promotion of an AI-authored policy. Fresh runtime authority/source checks and
private-to-Pages transport remain separate release work, as documented above.

## 2026-10-30 — approved beta navigation correction

VEDTATT: owner explicitly approves changing the 24 links on the single affected
beta page to existing catalogue navigation while retaining design/content. This
supersedes the preceding byte-preservation requirement only for those href values;
all other protected bytes remain protected. No merge/deploy/publication approved.

IMPLEMENTERT: `beta-navigation-adjustment.json` records the exact public page,
original/output bytes and SHA-256, 12 source URLs, 24 occurrences and `/k/` target.
Composition applies the correction only to a staging copy of that exact baseline,
only when the reviewed retirement includes all referenced product routes. The
original baseline/rollback archive is unchanged. Preservation accepts only this
specific before/after descriptor pair; arbitrary beta changes still refuse. The
private review report records the adjustment. No new input flag, workflow, rights,
renderer or generic beta rewrite mechanism is introduced. This is a one-time
website correction for the approved test catalogue, not a Core URL exception.

The replacement operates on exact href bytes, preserving visible text, images,
styles, structure and all other markup. It keeps beta noindex and does not index
its old demonstration content. Future catalogue groups use the same existing
composition; a baseline already containing the approved result needs no rewrite.

Learning: an approved exception to preservation should be a reproducible exact
before/after change, not a directory-wide waiver. Four focused regressions cover
link-only output, changed baseline, absent retirement, incorrect count/output and
one-way descriptor authorization. Existing catalogue/composition tests are reused.
The earlier observed beta blocker is resolved only when this exact adjustment and
the complete composed-site checks pass. Real product qualification, source freshness,
private transfer/release authority and public acceptance remain separate gates.

OBSERVERT validation: 26 focused local tests pass (4 link-adjustment, 14 existing
candidate, 8 composition). Integration using the original receiver, unchanged #304,
the actual reconstructed 128-file baseline and SYNTHETIC product catalogue passes
in both SEO modes: exactly 16 removals, 85 byte-identical beta files, one exact
24-link-only change, intact internal links, final-hash staging and wrong-hash refusal.
No real Toalson qualification or visual/public release acceptance is claimed.
One normal PR CI run follows push; unchanged Core/workflow checks are not rerun.

## 2026-10-30 — merge/publication boundary secured

VEDTATT: owner authorizes a bounded workflow correction so merge cannot publish;
public publication may only consume an explicitly approved, exact verified
Delivery candidate. No merge, deployment, grant or publication is authorized now.

OBSERVERT: prior pages.yml was active, non-documentation main pushes were
operational, and github-pages had only a main branch policy (no reviewer gate).
PR CI skipped deployment but merge could invoke the old API rebuild/publication.

IMPLEMENTERT: remove the legacy build/upload/deploy jobs from existing pages.yml
and the now-unused operational job output. Keep push/PR tests and the read-only
manual synthetic candidate verifier. No action can configure/upload/deploy Pages
from this workflow; no Pages-write or OIDC permission, publishing input or read-API
key remains. The renderer, other preview workflows, existing published website,
design, candidate hash checks and original Core/receiver pins are unchanged.
Existing preview artifacts are not Pages deployments and remain unchanged.

This deliberately closes publication; it does NOT claim that real publication
has been implemented. The existing upload-pages-artifact/deploy-pages integration
is preserved in Git history for reuse, not replaced by another publisher. No new
secret, token, service, permission, external setting or agent is introduced.
A workflow_dispatch, a candidate hash or an indexable flag cannot authorize release.

Required before a separately approved reconnection in this same workflow:
- real private input arrives through reviewed existing access, not public evidence
  artifacts; retain private receipts and only the publishable tree crosses;
- independently accepted FINAL hash binds the exact candidate to Property, release
  target, producer/consumer versions and reviewed baseline/current deployment;
- existing owner/native release authority is revalidated (expiry, revocation,
  revisions and target) at the publication boundary and recorded in audit;
- the existing Pages actions receive only those verified bytes, with no API build
  or beta regeneration between review and upload; concurrent deployment drift
  refuses and the verified previous release remains available for rollback;
- an ordinary merge, empty/incomplete dispatch or synthetic result cannot reach
  upload/deploy. Owner approval must be enforced, not an unverified boolean.

Four focused boundary tests check the checked-in workflow: its only jobs are
verification, write/deployment capabilities are absent, the API renderer/key is
disconnected, and manual candidate review retains synthetic/input/hash checks.
Other workflow files are checked for absence of Pages deployment capabilities;
their existing non-deploy preview artifact uploads are intentionally permitted.
Existing event-classifier behavior is unchanged; its workflow-wiring assertion
now requires the approved review-only Pages boundary instead of legacy build.
No catalogue/renderer changes or repeated catalogue test suite are needed here.

Learning: removing the unsafe event-to-publisher connection is the smallest safe
inactive integration when actual release authority/transport is not yet wired.
A disabled branch or self-declared approval is not verified release authorization.
Keep the unresolved operational integration explicit in #41/#304; no new engine,
new task or promoted active learning rule. This supersedes earlier text saying
ordinary main pushes retain the legacy Pages publication behavior.

OBSERVERT: all 19 focused workflow checks pass across the initial run and targeted
rerun of the corrected wiring assertion (14 unchanged event tests plus 5 boundary/
wiring checks). The initial failure was the obsolete test requiring automatic
Pages build; the replacement checks the approved absence of that path. No broad
catalogue suite repeated locally. Ordinary PR CI verifies the committed update.
