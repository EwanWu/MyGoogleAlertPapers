# Track A decision memo: `v2` vs `v2_narrow_antigarbage` (2026-04-21)

## 1. Question

Answer one narrow decision:

> On the same larger fixed seed, is `conditional_sources_v2_narrow_antigarbage` worth keeping over `conditional_sources_v2` as the default Track A patch?

## 2. Experimental basis

### Fixed seed
- source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- candidate count: `368`
- provider intents: `1405`

### Compared profiles
- baseline: `config/policy_profiles/conditional_sources_v2.yaml`
- treatment: `config/policy_profiles/conditional_sources_v2_narrow_antigarbage.yaml`

### Output artifacts
- `docs/validation/trackA-large-slice150-v2-replay-20260421.json`
- `docs/validation/trackA-large-slice150-v2-narrow-antigarbage-replay-20260421.json`
- `docs/validation/trackA-large-slice150-summary-20260421.json`
- log: `data/logs/trackA_large_slice150_20260421.log`

## 3. Top-line result

## Verdict

`conditional_sources_v2_narrow_antigarbage` **should not be kept as the new default** in its current form.

The reason is simple:
- canonical falls from `292` to `286` (`-6`)
- review rises from `4` to `5` (`+1`)
- merged proposals fall from `368` to `363` (`-5`)
- normalized-only fallback proposals fall from `39` to `31` (`-8`)

This means the patch is not just filtering obvious garbage. It is materially removing fallback-driven canonical outcomes that `v2` previously preserved.

## 4. Full metric comparison

| Metric | `v2` | `v2_narrow_antigarbage` | delta (narrow-v2) |
|---|---:|---:|---:|
| matched_source_record_count | 765 | 783 | +18 |
| merged_metadata_proposal_count | 368 | 363 | -5 |
| normalized_only_fallback_proposal_count | 39 | 31 | -8 |
| merge_review_queue_count | 4 | 5 | +1 |
| canonical_paper_count | 292 | 286 | -6 |
| severe_doi_conflict_count | 4 | 4 | 0 |
| cost_event_count | 2141 | 2136 | -5 |
| total_provider_latency_ms | 1,879,862 | 1,643,533 | -236,329 |

## 5. Why the patch regressed

The interesting point is that source matching did **not** get worse.

In fact:
- matched source records increased by `18`
- provider latency decreased modestly

So the regression is not an enrich-side failure.
The regression happens in **fallback acceptance policy**.

### 5.1 Canonical losses are concentrated in exactly 6 candidates

The full canonical loss (`-6`) is fully explained by these categories:

1. **Non-English title rejection**: `4` candidates
2. **Author-blob rejection**: `1` candidate
3. **False-positive author-tail pollution review**: `1` candidate

### 5.2 Non-English rule is the biggest driver

The current profile includes:
- `fallback_reject_non_english_title: true`

On this seed, that rule removes four previously-canonical fallback-only cases, including legitimate Chinese/Russian titles such as:
- `Современные возможности бесконтрастной МР-перфузии: от научных исследований до клинической практики`
- `食管鳞癌免疫微环境异质性及免疫治疗联合策略`
- `Роль интраоперационного внутрисосудистого ультразвукового исследования ...`
- `基于血管内超声分析载脂蛋白B 控制水平对冠状动脉斑块进展影响的队列研究`

This is not a narrow garbage-only effect.
It is a **scope policy** that removes non-English papers wholesale.

If the product goal is still broad scientific recall/correctness, this rule is too destructive for the default path.

### 5.3 Author-blob rejection caught one genuine garbage case

The rule:
- `fallback_reject_author_blob: true`

successfully removed one obvious bad fallback title:
- `Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3`

This is the cleanest part of the patch.

### 5.4 Author-tail pollution review produced one false positive

One legitimate English title was pushed from canonical to review:
- `Spironolactone, Early Acute eGFR Changes, and Clinical Outcomes in Patients with Heart Failure with Preserved Ejection Fraction: Insights from TOPCAT Americas`

In this case, the comma-rich title structure was interpreted as:
- `title_has_author_tail_pollution`

But the provider rows were simply DOI records with no provider title payload, so the salvage path could not rescue it.

This means the current author-tail rule is still too coarse for default use when fallback rows carry only identifiers and no title text.

## 6. What still worked inside Track A

Not everything failed.
There is one useful signal here.

### Successful salvage example

The patch successfully salvaged a real polluted-title case:
- candidate: `cand_1d53b41d67c6e37e`
- cleaned title:
  - `PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease`
- matched provider title similarity improved from `0.822` to `0.980`

So the **salvage concept** is still valid.
The problem is that the current combined profile couples:
- a broad scope rule (`non-English => reject`)
- a useful reject rule (`author_blob`)
- a still-imperfect review rule (`author_tail_pollution`)

## 7. Decision

## Default recommendation

Stay on:
- `conditional_sources_v2`

Do **not** promote:
- `conditional_sources_v2_narrow_antigarbage`

as the new default profile.

## 8. Recommended next move

If Track A continues, it should be split more narrowly:

### Keep as plausible next experiment
- retain the **author-blob reject** rule as a standalone micro-patch candidate

### Do not keep in the default anti-garbage patch
- blanket non-English title rejection

unless the system is intentionally moving to an explicit English-only collection policy

### Rework before re-testing
- author-tail pollution review should only fire when there is enough positive evidence for salvage or disambiguation
- DOI-only unmatched rows with empty provider titles are currently a bad fit for the present rule shape

## 9. Bottom line

Track A, in its current combined form, does **not** meet the keep criteria.

It does remove one obvious garbage case and demonstrates that salvage can work.
But on the formal larger fixed seed it still causes:
- lower canonical output
- higher review load
- loss of legitimate non-English papers
- one false-positive review on a valid English title

So the correct decision is:

> keep `v2` as the default, and only continue with a much narrower next patch if we want to iterate further.
