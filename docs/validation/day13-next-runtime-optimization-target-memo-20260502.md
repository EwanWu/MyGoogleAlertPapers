# Day13 next runtime optimization target memo (2026-05-02)

## Objective
After the Phase 2B promotions and the failed `select=` transport-side experiment, identify the **next genuinely promising runtime lever** for the current default workflow.

## What I checked

### Existing decision/runtime docs
- `docs/validation/day13-new-default-medium60-runtime-optimization-space-20260502.md`
- `docs/validation/day13-api-config-optimization-experiment-20260502.md`
- `docs/validation/day9-post-openalex-residual-audit-decision-20260430.md`
- `docs/21-phase2B-openalex-url-only-top5-reranking-decision-memo-2026-05-01.md`

### New audit artifact produced now
- `docs/validation/day13-medium60-post-openalex-residual-audit-20260502.csv`

Command used:
```bash
PYTHONPATH=src python3 scripts/export_post_openalex_residual_audit.py \
  --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
  --results-db data/benchmark/day2_baseline_small-fixed_day13-apikey-mailto-only-medium60-20260502.db \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml \
  --out-csv docs/validation/day13-medium60-post-openalex-residual-audit-20260502.csv \
  --slice-name day13_medium60_apikey_mailto_only \
  --reason openalex_title_unmatched
```

## Known

### 1. The remaining hotspot is already narrow
From `day13-new-default-medium60-runtime-optimization-space-20260502.md`:
- current wall time: `156847 ms`
- current provider latency: `151028 ms`
- residual `crossref:url_canonical_only` title requests after OpenAlex: `13`
- rough upper-bound savings if that tail disappeared: about `24 s`

So the remaining headroom is no longer architectural. It is concentrated in:
> `non-arXiv + url_canonical_only + openalex_title_unmatched -> residual Crossref title`

### 2. Broad transport-side tuning is not the answer
From `day13-api-config-optimization-experiment-20260502.md`:
- `api_key + mailto` is correct and retained
- OpenAlex/Crossref `select=` did **not** produce a reliable runtime win
- `select=` also degraded intermediate matching behavior and was rolled back

So the next lever should **not** be another generic transport shrinking tweak.

### 3. Earlier residual audit already pointed away from `cluster_leader_path`
From `day9-post-openalex-residual-audit-decision-20260430.md`:
- fixed150 + fresh30 high-confidence rescue subset was dominated by **OpenAlex recall-gap-like** cases, not by cluster-path overhead
- recommended direction was already: keep probing `url_canonical_only` rather than switching effort to `cluster_leader_path`

### 4. Top5 + reranking already harvested the obvious OpenAlex-local win
From `docs/21-phase2B-openalex-url-only-top5-reranking-decision-memo-2026-05-01.md`:
- once top5 was available, local reranking already reduced residual Crossref requests substantially
- that lever is already promoted into the current default

So the next lever is likely **not** “just ask OpenAlex a little better in the same way again.”

### 5. Current medium60 residuals are heavily URL-anchored publisher pages
New audit on the retained final run (`n=13` residual rows):
- heuristic buckets:
  - `likely_openalex_recall_gap = 5`
  - `possible_normalization_or_ranking_issue = 2`
  - `source_title_noise_or_crossref_cleanup = 4`
  - `mixed_or_unclear = 2`
- domain concentration:
  - `www.sciencedirect.com = 3`
  - `www.mdpi.com = 2`
  - `www.nature.com = 1`
  - `journals.lww.com = 1`
  - `www.cureus.com = 1`
  - remaining domains are singleton noise/mixed cases
- Crossref exact rescue signal inside the residual set is still material:
  - `7 / 13` residual rows have `crossref_matched = 1`

Representative residual URLs are not mostly random junk strings. Many are direct publisher landing pages or publisher PDF/reference variants.

### 6. Current code does not have a URL-origin DOI recovery lane
Current normalization only does passive regex extraction from existing text fields:
- `src/mygooglealertpapers/pipeline/normalize.py`
- `src/mygooglealertpapers/normalize/identifiers.py`

It does **not** do any of the following:
- landing-page DOI metadata recovery
- publisher-specific DOI inference from known URL shapes
- PDF/reference URL normalization into article landing URLs
- pre-provider DOI promotion from `url_canonical_only`

That means the current system still treats many URL-anchored candidates as title-search problems, even when the URL itself may carry stronger identity information than the title string.

## Inferred ranking of next-step options

### Option A — URL-origin DOI recovery micro-probe (**recommended**)
Mechanism:
- target only `non-arXiv + url_canonical_only`
- before OpenAlex/Crossref title fanout, try a **very narrow deterministic DOI recovery step** from `url_canonical`
- if DOI is recovered, promote candidate into the DOI path and bypass title search

Why this is the best next lever:
1. It attacks the residual subgroup at its root identity failure, not at provider ranking surface.
2. It can potentially remove **both** an OpenAlex title call and a Crossref title call for the same candidate.
3. It matches the observed residual anatomy: many remaining cases are URL-anchored publisher pages.
4. It avoids reopening broad policy behavior.

Important nuance:
- a broad “fetch every landing page HTML” design is **not** the best phase-1 move
- quick live checks showed some representative domains return `403` to simple script requests (`mdpi`, `sciencedirect`, `cureus`), so naive general HTML scraping may erase runtime gains or add brittleness

So the recommended version is:
> **deterministic URL-shape / URL-normalization / tiny whitelist DOI recovery first**, not broad page fetching first.

Good phase-1 candidates:
- Nature article/reference URL normalization (`.../articles/<slug>` / `..._reference.pdf`)
- Cureus article-id -> DOI heuristic where safely deterministic
- other publisher rules only if determinism is strong and local evidence supports them

Why this is still worthwhile even if the first whitelist is small:
- because it is a **new lane** that bypasses the whole title-search path
- even a few rescued cases matter once the residual tail is already down to ~13 groups on medium60

### Option B — narrow OpenAlex acceptance/query-shape debug for high-title-similarity rejects (secondary)
Mechanism:
- inspect cases where OpenAlex returned the same/nearly-same title but still ended up unmatched
- examples exist in the current residual set (`possible_normalization_or_ranking_issue = 2`)

Why secondary, not first:
- current medium60 residual composition shows only `2 / 13` such cases
- larger earlier audits also showed this is smaller than the recall-gap-like bucket
- so it is real, but not the largest remaining lever

### Option C — domain-conditioned OpenAlex skip / Crossref-first routing (not first choice)
Mechanism:
- for certain URL domains, skip OpenAlex title and go directly to Crossref title

Why not first choice:
- residual-only domain evidence is insufficient to prove those domains are globally poor for OpenAlex
- in the same medium60 sample, some of the same domains (`mdpi`, `sciencedirect`, `nature`, `lww`) also have OpenAlex **matched** cases
- a domain-only skip rule could easily save latency on failures while accidentally increasing Crossref load on current OpenAlex wins

So this is a plausible later ablation, but not yet the cleanest next experiment.

## Recommendation
The next genuinely promising optimization point is:

> **add a narrow URL-origin DOI recovery micro-lane for non-arXiv `url_canonical_only` candidates before the OpenAlex/Crossref title path.**

This is the first remaining lever that is both:
- mechanistically aligned with the residual failure mode
- narrow enough to test cleanly
- meaningfully different from the already-exhausted `select=` / top5 / reranking / suppression work

## Recommended experiment design
Run a one-factor ablation only.

### Control
Current default residual path.

### Treatment
For `non-arXiv + url_canonical_only` only:
1. attempt deterministic URL-origin DOI recovery from a tiny whitelist of URL patterns
2. if DOI recovered, route to DOI lane directly
3. otherwise fall back to the existing default unchanged

### Success bar
Keep the same semantic gate as prior promotions:
- no canonical drop
- no review increase
- no conflict increase

Primary operational readouts:
- `dispatch_request_count`
- `title_lane_request_count`
- `openalex` title events
- `crossref` title events
- `total_provider_latency_ms`
- residual `post_openalex_unsuppressed_targeted_group_count`

## Bottom line
The remaining problem is no longer “make provider payloads smaller” or “broaden suppression more.”
The next real opportunity is to stop treating some URL-anchored candidates as title-search problems at all.

That is why the best next target is:
> **URL-origin DOI recovery for the surviving non-arXiv `url_canonical_only` tail.**
