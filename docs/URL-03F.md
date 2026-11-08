# URL-03F — private visual model demonstration

This optional local tool renders the four owner-approved Baby Brezza models with
eight explicit color selections using the existing `build.product_body`, page
shell, `rich_ui.variants`, controlled image renderer and comparison table. No
production renderer, CSS, identity, taxonomy or deployment configuration changes.
The mobile menu receives an accessible name in this preview only; its existing
visual appearance stays unchanged.

Base: SjekkPris main `08892adf07b153e9b411a25b56477da736b6f663`.
Core contract: URL-03E `08d606a97c7f863141daf961207459da4a4e13c2`, already merged in Core.
Decision basis: SjekkPris Web Profile §§51/53, ADR-037/039, Chillout Web Standard
and the owner's explicit URL-03F approval. P08 is excluded, including as a default.

## Boundary and data provenance

The real review bundle is private and stays outside Git. It contains the exact
Property Delivery export/manifest bytes, eight URL-03E snapshot bytes/hashes and
a bounded local review expiry. The caller separately supplies the whole-file
SHA-256. The tool imports the original verifier from an existing clean checkout
at the pinned Core commit; it does not copy the contract or introduce a new model
registry. Existing canonical member IDs are preserved internally. A private model
reference never becomes a new canonical identity or a permanent route owner.

Preparation is an authorized private, read-only observation of the current
approved Property selection, followed by an offline URL-03E reconstruction and
verification. The deployed Core has no installed URL-03E DecisionSource. This
does **not** claim a successful live `capture`/`recheck_current`, a publication
lease, a new permission grant or production readiness. The data source uses two
equal existing export snapshots, explicit read-only transactions, active scoped
authorization reloaded before/after and no DML. Its safe collector and actual
catalogue data are private evidence, not a new checked-in data source or feed.

Color/item evidence must join the official manufacturer's exact variant ID to
the existing scoped Offer external ID, canonical binding and existing creation
audit. A generic model title, a valid GTIN checksum or a guessed color is not
enough. The private report records the evidence for each member, particularly
black Bottle Washer Pro. Without reviewed item evidence URL-03E supplies no
projection, so neither sibling image nor undocumented offers are displayed.
Only existing controlled Delivery images are loaded, with no referrer; no
provider images, marketing copy, health claims or guessed specifications are
imported. Unknown shipping/availability remain unknown even if the merchant's
current page makes stronger claims.

## Behavior

Each approved desired model path is served on loopback only. `?farge=...` is an
explicit member selection. A full document navigation replaces identity, image,
complete included/excluded comparison and existing source-designated price
winners together. No first/cheapest-color default, combined model from-price or
independent ranking. The bare path asks for a color and displays no arbitrary
member's image or prices. Invalid/duplicate/foreign selectors refuse, never fall
back. Back/reload/direct links retain the selection. Each color points to the
same absolute **local** canonical model URL; this assigns no public URL ownership.

Every response has `no-store`, `X-Robots-Tag: noindex, nofollow, noarchive`, a
restrictive CSP and no-referrer. HTML also has noindex; robots disallows all;
there is no sitemap. Host validation and loopback binding prevent network
exposure. No static export or directory serving can expose the private bundle.
Existing GTM/consent code is removed from preview output even with saved opt-in.
All commercial links terminate at the local disabled-action explanation.

The exact local bundle is re-read/reverified for each request. Removal, expiry,
inactivation, tampering, mixed source/specification revisions, Core refusal or
unavailable files fail closed. This local stop mechanism is **not** continuous
Core authorization/revocation: a frozen observation lasts at most 24 hours and
must be refreshed/reviewed after any relevant source/rights change.

## Run privately

Use a Python environment with Core's existing development dependencies and a
clean external checkout at the pinned commit. Supply only the existing controlled
image origin. There are no API credentials or DB connection parameters in this
consumer. Replace the sample paths with independently reviewed local files:

```text
python tools/model_preview.py --bundle /outside-repo/reviewed-bundle.json --sha256 <independent-whole-file-hash> --core-checkout /outside-repo/pinned-core --image-origin https://controlled-image-origin.example --port 18766
```

Real input and screenshots/results are refused inside this repository. Stop the
local helper process to close the preview. Do not run it on a shared server.

## Acceptance evidence

`python -m unittest discover -s tests -v` includes F01–F13. Some criteria have
multiple adversarial subcases; the renderer fixture verifier is explicitly a
test seam, not a replacement for Core verification or authoritative evidence.
The real CLI has no fixture-verifier switch.

| Criterion | Evidence |
|---|---|
| F01 | All eight exact members, model heading, selected color, selected image and one query-free canonical |
| F02 | Unknown color refused; no first-member fallback |
| F03 | Bare model path has chooser, no default image or offers |
| F04 | Missing reviewed item evidence suppresses entire image/comparison projection |
| F05 | Input unchanged; no GTM, tokens or real commercial target even with saved consent |
| F06 | Edited local bundle invalidates existing reader |
| F07 | Removed local bundle invalidates existing reader |
| F08 | Inactive, expired, future or overlong review refused |
| F09 | Otherwise valid foreign Property, environment and locale refused |
| F10 | Mixed revision, missing or duplicate member refused |
| F11 | Pending package and sibling image refused |
| F12 | Rejected rendering leaves exact input bytes unchanged |
| F13 | HTTP refusal is atomic; host/query/traversal/security headers and unavailable/Core-refused data tested |
| F14 | All 8 colors × 390/1280: direct link and reload |
| F15 | Keyboard switch and back navigation replace the complete selected state |
| F16 | Correct image loaded and full included/excluded comparison rows match selected source |
| F17 | Canonical/noindex, no analytics/operative clickouts; shipping switch retains selected basis |
| F18 | Axe WCAG 2/2.1 A/AA, selected ARIA state, focus indicator, 44px color controls, image alt and no viewport overflow |
| F19 | All 16 screenshots plus machine-readable browser result; no unexpected outgoing requests |
| F20 | Byte-identical input after complete browser loop; unknown/bare routes and local disabled-action page |

Synthetic browser run (Playwright 1.58.0, Chromium; axe-core 4.10.3):

```text
python tools/check_model_preview.py --out /tmp/model-proof --axe /path/to/axe.min.js
```

Real browser run adds the same bundle/hash/Core/image-origin arguments as the
server. GitHub CI runs **synthetic data only**, with no secrets, artifact upload,
Pages build, publication or deployment. Real screenshots and evidence are
delivered in a separate local private report.

## Remaining production work

Public permanent model-route ownership is not established by this tool or by
URL-03E. Production still needs an explicitly approved ownership/alias-history
solution compatible with the existing registry, current authorization/revocation
and source rechecks at the real build/publication boundary. Complete category
routes and documented redirects remain separate. P08 needs package evidence.
Additional descriptions, price history, guides and more merchants can wait;
missing facts are left empty in this demonstration. No new generic platform
module is required to review these four pages.
