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
Any missing old file, changed existing CSS/JS, assets or beta refuses the candidate.
Shared homepage/search/category content changes are reported in the full diff,
not silently accepted as publication authority. Review this diff for expected
new membership and unrelated product changes before release. Core hash verification
does not prove live revocation checks or ownership of a public URL.

No renderer reruns after receipt. Existing qualified renderer already produces
product, search and category surfaces from one input. It must be supplied the
FULL qualified catalogue: a one-product private build is not a replacement for
the current live catalogue. Withheld products must never be silently republished
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
candidate that loses old routes is refused. Before the first live catalogue,
existing route ownership/aliases must be reconciled using the existing registry
and reviewed redirects where necessary. Core's private renderer currently also
uses `/sok/` and `/k/`; old `/search/` and `/kategori/` must not disappear unnoticed.

No CSS/layout/template or price/ranking formula changes. Head metadata and exact
clickout prefix are the only HTML rewrites. Mobile/design/browser acceptance on
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

Remaining first-delivery gates: full baseline; full qualified input preserving old
catalogue/URLs/beta; actual limited SQL-role acceptance and fresh short owner grants;
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
