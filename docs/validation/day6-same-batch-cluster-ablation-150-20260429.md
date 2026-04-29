# Day 6 same-batch candidate clustering ablation (150 synthetic-duplicate stress slice, 2026-04-29)

## Goal

Measure whether **exact same-batch candidate clustering** adds meaningful runtime savings on top of the already-promoted synchronous default:

- exact `library_prelink`
- `identifier_fastpath + title_core`

This experiment targets the case that Phase 1 does **not** solve:

> the same paper recurs multiple times **inside the same batch**, but the batch is not yet deduplicated before enrich.

## Setup

### Base profile

Control and treatment both preserve:

- promoted synchronous lane shape: `identifier_fastpath + title_core`
- exact `library_prelink_enabled: true`

### Only treatment difference

Treatment additionally enables:

- `same_batch_clustering_enabled: true`

### Data construction

Source seed:

- `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`

Prepared replay slice:

- base candidates: `120`
- synthetic duplicates appended: `30`
- replay candidate count: `150`

Synthetic duplicate design:

- preserve exact `url_canonical` / `scholar_cluster_hint` when present
- remove DOI / PMID / PMCID / arXiv on the duplicate row
- mutate title into a variant string

This intentionally creates a stressful intra-batch scenario where:

- control cannot use identifier fastpath on the duplicate row
- treatment can cluster the duplicate onto the leader and reuse the leader's provider intents / results

## Profiles

### Control
- `config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml`

### Treatment
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`

## Known results

### Control
- status: `ok`
- total batch duration: `586361 ms` (~`9.77 min`)
- total provider latency: `581879 ms`
- provider intent count: `306`
- matched source record count: `223`
- canonical paper count: `106`
- merge review queue count: `0`
- severe DOI conflict count: `0`
- dispatch request count: `226`
- dispatch groups: `264`
- title-core dispatch requests: `180`
- same-batch clustering: disabled

### Treatment
- status: `ok`
- total batch duration: `447053 ms` (~`7.45 min`)
- total provider latency: `443547 ms`
- provider intent count: `306`
- matched source record count: `252`
- canonical paper count: `105`
- merge review queue count: `0`
- severe DOI conflict count: `0`
- dispatch request count: `178`
- dispatch groups: `216`
- title-core dispatch requests: `132`
- same-batch cluster groups: `30`
- same-batch clustered candidates: `44`
- cluster rule counts:
  - `url_canonical_exact_cluster`: `23`
  - `doi_exact_cluster`: `20`
  - `pmcid_exact_cluster`: `1`

## Direct comparison

### Runtime / request savings

Control -> Treatment:

- total batch duration: `586361 -> 447053 ms`
  - improvement: `139308 ms`
  - relative reduction: `23.8%`
- total provider latency: `581879 -> 443547 ms`
  - improvement: `138332 ms`
  - relative reduction: `23.8%`
- dispatch groups: `264 -> 216`
  - reduction: `48`
  - relative reduction: `18.2%`
- dispatch requests: `226 -> 178`
  - reduction: `48`
  - relative reduction: `21.2%`
- title-core dispatch requests: `180 -> 132`
  - reduction: `48`
  - relative reduction: `26.7%`

### Crossref / OpenAlex latency movement

Provider totals:

- `crossref`: `384613 -> 302040 ms` (`-82573 ms`, `-21.5%`)
- `openalex`: `186742 -> 132663 ms` (`-54079 ms`, `-29.0%`)

## Interpretation

### Known

1. Exact same-batch clustering produced a **real runtime win** even after exact library-first prelink was already in place.
2. The savings were concentrated where expected: **title_core**.
3. Review burden did **not** worsen:
   - merge review queue stayed `0`
   - severe DOI conflict stayed `0`
4. This is not merely “dispatch bookkeeping improvement”; wall time dropped by about **2.32 minutes** on the 150-candidate synthetic stress slice.

### Inferred

1. The same-batch layer is worth keeping as the **next runtime-control layer after exact prelink**.
2. The main value proposition is not abstract dedup purity; it is concrete suppression of repeated **title-lane** work for same-article duplicates that arrive together.
3. The stronger treatment matched-source count (`223 -> 252`) suggests that leader identifier intents can also improve evidence quality for duplicate variants that would otherwise rely on weaker title fallback.

### Caution

This experiment used a **synthetic duplicate stress slice**, not a fully natural mailbox slice.
So the exact percentages should not be promoted as universal production expectations.
What is safe to promote is the directional conclusion:

> same-batch exact clustering is a meaningful and low-risk next layer above Phase 1 exact library prelink.

## Decision

Promote the following staged architecture as the current fixed workstream order:

1. **exact library-first prelink**
2. **same-batch exact candidate clustering**
3. residual `identifier_fastpath + title_core` runtime optimization
4. continued `crossref` title-lane cost reduction

## Artifact paths

- control JSON: `docs/validation/day6-same-batch-cluster-control-150-20260429.json`
- treatment JSON: `docs/validation/day6-same-batch-cluster-treatment-150-20260429.json`
- treatment profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- task state: `data/task_state/same_batch_cluster_experiment_20260429.json`
