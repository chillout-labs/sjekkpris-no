# URL-03J — reviewed variant discovery (private integration)

Owner decision 2026-10-25: explicit reviewed black default for all four current
model presentations, with exact member identity and evidence revision. No
default inferred by this component. Callers supply `variant_choices` in approved
default-first order; each choice is one complete source projection. The Core
offline readiness adapter validates its independently pinned human decision.
This display interface grants no authority and is not an operative approval API.

Existing card, search, product template and controls are reused. One model card
shows one member's image, price and link, with “Andre farger tilgjengelig”. Search
matches documented member names/colors, choosing the approved default for generic
queries. No color page or new identity is created. Bare model and color queries
retain one canonical. Missing member evidence never borrows another member's
image/price. Native disclosure shows six choices and retains the selected member
outside it; all remaining choices are available to keyboard and touch users.

This branch is stacked on unchanged Draft #37 (`a0fef162`), whose main base was
rechecked at `08892adf`. #37 remains untouched. Core Draft #268 pins the new
component commit and supplies binding, expiry, revocation and private noindex.
The original URL-03E/G/H contracts continue to refuse inferred defaults and
untrusted authority; the new owner choice exists only in the private J envelope.
Future operative default decisions must use current Core/Delivery approval and
complete artifact/revision binding, never this view model as evidence.

Acceptance: complete unit suite; browser 2/20 colors at 390/1280, generic and
color-specific search/reset, exact one image/price/link; selected member visible,
keyboard disclosure. Core #268 adds actual frozen eight-member browser checks,
default bare/direct/reload/canonical/noindex and withdrawn input refusal.
P08 is excluded by the caller. No live build caller or publishing flag changes.

## Independent final review, 2026-10-25

Confirmed P2 cases were reproduced before correction: a default `Farge 10`
could win a full search for `Farge 1`; and suggestion JSON retained an image
that the existing card image validator rejected. Exact full names and documented
color labels now precede partial matches, while generic searches retain the
explicit default-first order. Both search surfaces share that selection logic.
Search/card entries share the existing public image validator and refuse unsafe
non-internal color links before rendering. No new image host allowance is added.

Regression coverage now includes a 20-color model with explicit default 10,
full/short exact searches for color 1, color 19, generic reset, suggestions and
keyboard disclosure at both widths; rejected images and unsafe links; complete
107-case unit suite. Core #268 independently compares each displayed offer's
advertiser, amount and exact `/go/` target against the selected source snapshot.
