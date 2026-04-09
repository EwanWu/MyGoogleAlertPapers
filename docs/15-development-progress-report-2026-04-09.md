# Development Progress Report (2026-04-09)

## Scope
Review the current state of the email-driven literature database project (`MyGoogleAlertPapers`) by combining:
- prior session memory
- local repo docs
- current codebase
- validation artifacts
- current git state

Project path:
- `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers`

---

## 1. Executive summary
The project is no longer a planning-only repo. It already has a working local-first pipeline:

`scan mailbox -> parse mails -> normalize candidates -> enrich metadata -> merge metadata -> deduplicate into canonical papers`

Current state is best described as:
- **pipeline prototype functional on real mailbox data**
- **execution-control hardening partly completed**
- **correctness hardening actively underway**
- **documentation is ahead of README and largely reflects the real state**

The main strategic shift since earlier planning has been correct: the bottleneck is no longer “can the pipeline run?” but rather:
1. can enrichment resume reliably,
2. can cache behavior be trusted,
3. can wrong DOI/PMID attachments be reduced,
4. can the canonical store stay conservative under conflict.

---

## 2. What is already implemented

## 2.1 End-to-end CLI pipeline exists
Code entrypoint:
- `src/mygooglealertpapers/cli.py`

Implemented commands include:
- `init-db`
- `scan-mailbox`
- `parse-mails`
- `normalize-candidates`
- `enrich-candidates`
- `merge-metadata`
- `dedup-candidates`
- reporting commands for batch / normalization / enrichment / merge / dedup / cost

This means the repo has already crossed the line from design into runnable workflow.

## 2.2 Database schema has matured beyond the original skeleton
Schema file:
- `src/mygooglealertpapers/db/schema.py`

Important implemented tables include:
- `mail_ingestion_record`
- `raw_mail_snapshot`
- `paper_candidate`
- `paper_candidate_normalized`
- `query_cache`
- `source_record`
- `candidate_enrichment_status`
- `merged_metadata_proposal`
- `canonical_paper`
- `candidate_paper_link`
- `cost_event`

Notable point:
- `candidate_enrichment_status` and unique cache key enforcement are already present, which means Package 1 and Package 2 are not just planned, they are largely coded.

## 2.3 Enrichment layer is materially richer than before
Current providers in code:
- Crossref
- OpenAlex
- PubMed
- Semantic Scholar

Important implemented behavior in `pipeline/enrich.py`:
- provider-level work intent construction
- provider-level resumability logic via `candidate_enrichment_status`
- cache lookup before external request
- OpenAlex DOI batch path
- structured handling of `ok` / `no_match` / `error`
- source record persistence for both matches and no-match outcomes

This is a substantial step up from the earlier candidate-level prototype.

## 2.4 Merge logic is implemented but still intentionally simple
Current merge stage in `pipeline/merge.py`:
- chooses preferred metadata by source priority
- tracks per-field trace
- records conflict flags
- writes merged proposals
- currently uses a coarse confidence rule (`0.9` if no conflict else `0.6`)

Interpretation:
- merge is operational
- merge judgment is still relatively crude
- the next real gains likely come from conflict grading rather than more threshold tweaking alone

---

## 3. What has been validated so far

## 3.1 Earlier 100-email validation established that the pipeline works at scale-relevant small batch size
Validation doc:
- `docs/validation/issac-100-validation-report.md`

Observed in that run:
- scanned mails: 100
- Scholar mails: 66
- candidates: 244
- source records: 732
- matched source records: 532
- merged proposals: 235
- proposals with conflicts: 146
- canonical papers: 205

Interpretation:
- throughput and basic orchestration work
- conflict burden was still very high
- canonical layer was exposed to obviously wrong identifier assignments in some cases

## 3.2 30-email recheck showed enrichment was the main runtime bottleneck
From prior recorded run:
- enrichment dominated runtime (~342 s)
- rerun after completed enrichment became very fast (~0.19 s)

Interpretation:
- cache/resume work was correctly prioritized
- runtime pain is mainly provider interaction, not local processing

## 3.3 Package 1 and Package 2 appear implemented and validated at first pass
Relevant docs:
- `docs/12-package-1-resumability-spec.md`
- `docs/13-package-2-cache-hardening-spec.md`
- `docs/validation/package2-targeted-validation.md`

Supported claims from docs + code:
- provider-level enrichment status is in schema and repository code
- rerun selection is provider-level, not candidate-level
- query cache has unique key `(provider, query_type, query_key)`
- cache writes are upsert-based
- small-slice validation reported zero duplicate cache keys after rerun

Current caveat:
- durable checkpointing is still not finest-grained under hard kill before transaction commit

## 3.4 Package 3 correctness work has moved beyond planning and produced real improvement
Relevant docs:
- `docs/14-package-3-correctness-plan.md`
- `docs/validation/package3-workstream-a-control-vs-treatment.md`
- `docs/validation/package3-iter2-fix-30.md`
- `docs/validation/package3-fix-60-summary.md`

Important trajectory:
1. First Package-3 threshold-tightening pass produced little or no improvement.
2. Second targeted fix did help materially.
3. Larger 60-mail slice suggests the error profile is better than before.

Key 30-mail iterative-fix result:
- conflicts improved from `34 -> 24`
- canonical papers `46 -> 45`
- PubMed matched fewer records, suggesting more conservative fallback
- Semantic Scholar became a useful complementary provider

Key 60-mail summary:
- normalized candidates: 135
- matched source records: 288
- merged proposals: 114
- proposals with conflicts: 46
- canonical papers: 101

Interpretation:
- correctness work is now producing real signal
- project is in a better state than the earlier 100-mail run
- remaining issues are harder ambiguity cases, not just obvious false overrides

---

## 4. Current codebase reality vs docs

## 4.1 The docs are mostly ahead of README
`README.md` still says:
- `Status: Planning / pre-implementation`

That is now outdated.

Actual state from code and validation is closer to:
- implemented prototype with repeated real-mailbox validation
- partial hardening completed
- correctness refinement in progress

## 4.2 Git history shows a meaningful implementation sequence
Recent commits:
- `ecf781c` feat: harden authoritative query cache behavior
- `385b9b8` feat: add provider-level enrichment resumability foundation
- `47d20b0` feat: improve enrichment observability and provider request shaping
- `5d9e83a` docs: add enrichment reliability hardening plan
- `e5acf64` feat: add batch timing and reusable enrichment cache

Interpretation:
- work sequence is coherent
- docs-first diagnosis was followed by execution-control hardening
- then correctness iteration began

## 4.3 There are still uncommitted working-tree changes
Modified tracked files include:
- `src/mygooglealertpapers/config.py`
- `src/mygooglealertpapers/enrich/base.py`
- `src/mygooglealertpapers/enrich/crossref.py`
- `src/mygooglealertpapers/enrich/openalex.py`
- `src/mygooglealertpapers/enrich/pubmed.py`
- `src/mygooglealertpapers/mail/candidate_extractor.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/merge.py`

Untracked items include:
- validation outputs in `data/`
- validation docs under `docs/validation/`
- `src/mygooglealertpapers/enrich/semanticscholar.py`
- `tests/test_candidate_parser_quality.py`
- `docs/provider-optimization-note.md`
- `docs/14-package-3-correctness-plan.md`

Interpretation:
- the repo contains important progress not yet packaged into a clean commit sequence
- the current state is valuable but still somewhat mid-flight

---

## 5. Main technical strengths right now

1. **The pipeline is real, not hypothetical.**
2. **The project has good observability** through batch, merge, enrichment, dedup, and cost reporting.
3. **Resumability and cache authority were attacked in the right order.**
4. **Validation is empirical**, using real mailbox slices rather than only unit tests.
5. **Correctness work is being done conservatively**, which fits the project goal of a trustworthy main store.
6. **Provider diversification improved the evidence mix**, especially with Semantic Scholar as a cautious complement.

---

## 6. Main weaknesses / risks still open

## 6.1 Merge confidence remains too coarse
Current merge confidence in `pipeline/merge.py` is still basically binary:
- no conflicts -> `0.9`
- any conflicts -> `0.6`

This is too weak to represent:
- benign formatting differences
- mild metadata divergence
- severe DOI/PMID contradiction

## 6.2 Hard-kill durability is still incomplete
Provider-level resumability exists, but transaction durability still means a badly timed kill can roll back in-flight work.

This is acceptable for now, but it is not yet full checkpoint durability.

## 6.3 Validation environment reproducibility is incomplete
I attempted to run tests in the current environment and hit:
- `pytest: command not found`

Implication:
- test suite exists, but the local runtime is not yet fully packaged for one-command reproducibility
- `pyproject.toml` also has minimal dependencies and no dev/test extras

## 6.4 README/project status messaging is stale
The repo understates current maturity, which makes it harder to reason about current priorities quickly.

## 6.5 Remaining hard cases are now concentrated in truly ambiguous zones
Examples from docs indicate the remaining conflict classes include:
- no DOI on candidate side
- title-based providers disagreeing on DOI
- venue-label formatting noise
- HTML / Unicode residue
- preprint vs journal vs version-like ambiguity

This is good news in one sense: the grossest failure mode has been reduced.
But it also means future gains will likely be slower and require better judgment logic, not just more providers.

---

## 7. My assessment of current project stage

Best label:
- **late prototype / early hardening stage**

Not yet:
- production-grade
- fully reproducible
- trustable enough for large blind scale-up

Already beyond:
- planning
- toy skeleton
- one-off experiment

A more honest status line would be:
- **Working prototype validated on real mailbox slices; now in resumability, cache-authority, and correctness hardening.**

---

## 8. Recommended next-step options

## Option A — finish Package 3 properly (recommended)
Focus next on:
1. merge conflict grading (A/B/C severity)
2. conservative canonicalization guardrails for severe conflicts
3. normalization cleanup for HTML / Unicode residue
4. targeted review set for remaining hard cases

Why this is best:
- Package 1 and 2 already changed execution behavior materially
- Package 3 has started to show real gains
- the biggest remaining risk is false certainty in canonical records, not lack of providers

## Option B — clean the repo and freeze a checkpoint release
Focus next on:
1. commit current untracked/modified work cleanly
2. update README status
3. add reproducible dev/test setup
4. tag a milestone

Why this is valuable:
- reduces context debt
- makes later experimentation safer and easier to compare

Risk:
- improves project hygiene more than correctness itself

## Option C — run a larger validation slice now
Focus next on:
1. freeze current code
2. run 100-mail or larger comparative validation
3. sample conflict cases systematically

Why this is tempting:
- gives stronger empirical signal

Why I would not do it first:
- merge/canonical guardrails still look too coarse
- larger runs now may mostly generate more ambiguous error examples rather than fundamentally new insight

---

## 9. Recommendation
I recommend this order:
1. **finish Package 3 merge/canonical protection**
2. **clean and commit the current working tree into coherent checkpoints**
3. **then run a larger validation slice (60 -> 100 or more) with systematic error sampling**

Concretely, the highest-value next coding target looks like:
- implement conflict severity grading in merge
- block or downgrade severe-conflict canonical promotion
- add a small review export for ambiguous merged proposals

---

## 10. Known / inferred / speculative

### Known
- repo path is `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers`
- end-to-end CLI pipeline exists
- provider-level status and authoritative cache behavior are implemented in code
- real validation docs exist for 10, 30, 60, and 100-mail slices
- current merge confidence remains coarse
- working tree is not clean
- local environment currently lacks `pytest`

### Inferred
- Package 1 and Package 2 are effectively completed first-pass implementations
- Package 3 is mid-flight but no longer exploratory only
- remaining quality gains depend more on judgment and grading than on adding providers

### Speculative
- a lightweight manual-review export for severe conflicts may deliver a better return than more threshold tuning
- after merge grading is added, a larger validation run may show a disproportionate quality improvement even if recall changes little

---

## 11. Bottom line
This project has already made the transition from concept to functioning research data-ingestion system.

The current frontier is no longer “make it run.”
It is “make it conservative, resumable, and trustworthy enough to scale without poisoning the canonical store.”
