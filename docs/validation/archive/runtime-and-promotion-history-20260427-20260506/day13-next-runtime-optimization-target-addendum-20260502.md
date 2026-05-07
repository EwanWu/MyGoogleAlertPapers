# Day13 next runtime optimization target addendum (2026-05-02)

## Why this addendum exists
After the first day13 memo identified **URL-origin DOI recovery** as the next promising direction, I pushed one level deeper to test which sub-variant is actually worth implementing first.

## Additional probes run

### 1. Medium60 residual URL fetch probe
I attempted lightweight DOI recovery directly from the current `13` residual URLs in:
- `docs/validation/day13-medium60-post-openalex-residual-audit-20260502.csv`

Observed:
- `nature.com/articles/..._reference.pdf` yielded the correct DOI directly
- many high-value publisher pages (`mdpi`, `sciencedirect`, `cureus`, `lww`, `thelancet`) returned `403` to a simple script request
- so **broad HTML/page fetch is not the right phase-1 design**

### 2. Recursive URL decode probe on the source slice
I checked whether the current normalization misses DOIs hidden in URL-encoded strings.
Result on the slice150 source DB:
- recoverable via recursive decoding but currently missed: `1` case total
- candidate: `cand_8c0fcffbabdce4e6`
- URL: `https://www.e-ultrasonography.org/journal/view.php?doi%3D10.14366%252Fusg.23232`
- recursively decoded DOI: `10.14366/usg.23232`

Interpretation:
- this is real and worth folding into a URL-identity patch
- but by itself it is too small to be *the* main optimization story

### 3. Residual-failure mechanism decomposition
I decomposed why OpenAlex title results were still unmatched in the residual audit.

#### Large fixed audit (`n=52` residual rows)
- `title + family + venue` failure: `31`
- `title` failure only: `15`
- `title + family`: `3`
- `venue` only: `2`

#### Current medium60 audit (`n=13` residual rows)
- `title + family + venue` failure: `6`
- `title` failure only: `5`
- `title + family`: `1`
- `venue` only: `1`

Interpretation:
- a narrow **OpenAlex venue-veto relaxation** patch is real but small
- it is not the dominant remaining mechanism

### 4. PII probe on ScienceDirect URLs
I tested whether `sciencedirect` PII strings could act as a practical provider query key in Crossref/OpenAlex search.
Quick probe on representative residual PIIs did **not** surface useful results.

Interpretation:
- a new generic `PII` identifier lane is not currently the best next move

## Refined conclusion
The original day13 memo was directionally right, but this deeper pass sharpens it:

> The next genuinely promising optimization is **not** generic page fetching, **not** a new PII lane, and **not** venue-rule tweaking.

It is:

> **a deterministic URL-identity micro-lane inside `non-arXiv + url_canonical_only`**

with the following priority order.

## Recommended priority order

### Priority 1 — deterministic URL-shape DOI / article-identity recovery (**best next step**)
Target only patterns that are cheap and deterministic, for example:
- recursive URL decoding for hidden DOI query parameters
- `nature.com/articles/..._reference.pdf` → article slug / DOI recovery
- other low-risk publisher-specific URL rewrites only when the mapping is deterministic

Why first:
- avoids title search altogether when it works
- low runtime overhead
- does not depend on fragile page fetches
- aligns with the observed residual structure

### Priority 2 — tiny whitelist metadata fetch only for fetch-friendly patterns/domains
Only after deterministic URL parsing is exhausted.

Why second:
- the residual fetch probe showed many important domains block simple scripted requests with `403`
- so “fetch all landing pages” is too expensive and too brittle as a first implementation

### Priority 3 — narrow OpenAlex acceptance relaxation for repository-hosted exact-title hits
Candidate example already observed:
- exact title + correct author + correct DOI present in OpenAlex result
- but rejected because venue hint conflicts with repository host source

Why third:
- real but small (`1/13` current medium60 residuals; `2/52` large-fixed residuals)
- worthwhile only after the URL-identity path is tested

## Bottom line
If the question is “what is the next layer that actually still has runtime upside,” the refined answer is:

> **deterministic URL parser / DOI recovery before title fanout**

not a broad network-fetch lane, not a PII lane, and not more provider payload tuning.
