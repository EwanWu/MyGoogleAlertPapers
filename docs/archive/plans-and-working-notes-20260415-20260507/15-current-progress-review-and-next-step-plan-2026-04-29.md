# Current progress review and next-step plan (2026-04-29)

## Objective

Reconstruct the real current project state after context loss by checking:
- active docs
- recent validation artifacts
- current git history
- current uncommitted code/docs state
- current test status

---

## Executive summary

The project is **past policy exploration** and is now split into two active workstreams:

1. **Mainline bibliographic pipeline is already stable enough to be the default**
   - core default: `conditional_sources_v2 + author_blob_fallback_only + post-dedup enrich-paper-oa`
   - Day 2 / Day 3 runtime hardening and title-payload-reuse promotion are already in place
   - deterministic replay evidence for narrow optimization promotion is strong

2. **The next real bottleneck is throughput architecture, not matching policy**
   - OpenAlex DOI batching itself is working as expected
   - large live enrich still times out because the full provider fanout is effectively near-serial
   - Semantic Scholar is the primary current live bottleneck
   - after removing Semantic Scholar, Crossref + PubMed/EuropePMC-class title lookups become the next bottleneck class

A secondary but real parallel workstream also exists:

3. **163 Windows-local acquisition is operational, but body-fetch speed still needs UI-navigation reduction**
   - indexing works
   - body sweep works and can already ingest into SQLite
   - current near-term best path is A+B (`history.back` + page-resident sweep)
   - medium-term performance ceiling is C (`read_mid`-driven direct fetch / hybrid)

---

## What is firmly completed

## A. Mainline policy decision layer is settled

### Known
- `docs/14-mainline-promotion-memo-2026-04-22.md` promotes:
  - `conditional_sources_v2`
  - `conditional_sources_v2_author_blob_fallback_only`
  - `post-dedup enrich-paper-oa`
- `docs/13-project-phase-map-and-current-status-2026-04-22.md` explicitly says the project is no longer mainly exploring strategy space
- Track B is closed as a policy question: Unpaywall stays post-dedup, not candidate-level enrich

### Interpretation
The project should **not** spend the next phase reopening broad matching heuristics unless fresh evidence shows correctness breakage.

---

## B. Day 2 / Day 3 hardening landed successfully

### Known
Recent committed history:
- `03db1fa` harden local import + benchmark baseline
- `e0e4311` provider HTTP client + enrichment plan report
- `005f8a1` plan recommendations + crosschecks
- `0b2caf7` safe dispatch dedup
- `3f4c6bd` context-aware enrichment cache keys
- `650b3af` HTTP fixture record/replay + title payload reuse optimization
- `53d5997` title payload reuse default-enabled
- `8c126a6` docs consolidation

### Known from validation
- `docs/validation/recorded_deterministic_ab_medium60_20260427.md`
  - title payload reuse on the current narrow scope passed deterministic replay
  - candidate-level semantic drift = `0`
- `docs/validation/day3-enrichment-plan-snapshot-slice150-20260427.md`
  - current biggest remaining request-reduction opportunity is OpenAlex DOI batching
  - expected `127 unique DOI -> 3 batch requests`

### Interpretation
The current mainline is not a fragile prototype anymore. It has:
- benchmark/replay entrypoints
- runtime dedup
- context-aware cache semantics
- deterministic replay promotion discipline

---

## C. 163 local ingestion boundary is solved

### Known
From docs and committed workflow:
- Windows-local 163 index flow is validated
- body fetch emits import-compatible JSONL
- local body ingestion into SQLite boundary is proven
- the acquisition/enrich phases are now correctly decoupled

### Interpretation
For 163 acquisition, the unsolved problem is no longer “can we connect it into MGAP?”
It is now “how do we reduce body-fetch UI cost enough for larger-scale sustained runs?”

---

## What is currently in-progress but not fully folded into the active layer

## A. Day 4 throughput diagnosis is real and important

### Known
There are untracked but substantive validation artifacts:
- `docs/validation/day4-openalex-batching-baseline-slice150-20260427.*`
- `docs/validation/day4-openalex-batching-observed-slice150-20260427.*`
- `docs/validation/day4-ablation-baseline-120-20260427.*`
- `docs/validation/day4-ablation-no-semanticscholar-120-20260427.*`
- `docs/validation/day4-ablation-comparison-120-20260427.md`
- `docs/validation/day4-timeout-diagnosis-and-scale-plan-20260427.md`

### What these establish
1. slice150 live enrich timeout is **not** evidence that OpenAlex batching failed
2. OpenAlex batching reached the expected batch shape
3. the real scale failure is effective near-serial live fanout across slow providers
4. Semantic Scholar is the first provider that should probably leave the synchronous default lane

### Strongest direct evidence
From `day4-ablation-comparison-120-20260427.md`:
- baseline: `250 / 474` processed intents in timeout window
- no-semanticscholar: `325 / 354`
- completion fraction jumps from `52.7%` to `91.8%`
- projected full runtime drops from `17.39 min` to `10.79 min`

### Interpretation
This is the most decision-relevant new result after Day 3.
The next phase should be framed as **provider-lane architecture / throughput control**, not more match-policy churn.

---

## B. Timeout-safe observability code is already being added

### Known from working tree diff
Modified but uncommitted code:
- `scripts/replay_validation.py`
- `src/mygooglealertpapers/db/repository.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/enrich_stats.py`
- `tests/test_enrich_cache_semantics.py`

### What these code changes do
- persist in-flight `batch_run` progress during enrich
- store `processed_runnable_intents`
- distinguish:
  - `request_savings_vs_processed_intents`
  - `request_savings_vs_total_planned_intents`
- make timeout reports interpretable instead of misleading

### Validation status
- targeted tests pass: `tests/test_enrich_cache_semantics.py`
- full test suite passes: `PYTHONPATH=src python3 -m pytest tests -q`

### Interpretation
This is not cosmetic. It is the instrumentation needed to make long-timeout partial runs scientifically interpretable.
It should probably be committed before the next experiment wave.

---

## C. 163 body-fetch optimization state is real but not yet reflected in active project map

### Known
A new analysis doc exists:
- `docs/validation/163-local-body-fetch-three-schemes-analysis-20260428.md`

### Current conclusion
- **production-now:** A+B
- **medium-term optimization:** C hybrid (`read_mid` direct fetch where available, fallback otherwise)

### Interpretation
This workstream is valid, but it is secondary to the central throughput problem inside the bibliographic enrich pipeline.
Unless the immediate goal is large new local acquisition, this should remain a parallel or later sprint.

---

## Current project-state judgement

## Known
If I collapse code + docs + validations together, the project is currently in:

> **mainline stable, runtime-observable, but not yet scale-stable**

That means:
- correctness-side default policy is in a good place
- narrow runtime optimizations can now be promoted safely via replay evidence
- throughput on larger live runs is still not operationally robust
- the next step is no longer “invent a better policy”, but “re-architect live provider execution order and budget”

## Inferred
The next major win will probably come from **provider demotion / lane splitting / partial async design**, not from another micro-heuristic.

## Speculative
If Crossref + biomedical title-fallback lanes are still too expensive even after Semantic Scholar demotion, the project may need a local-first or cache-first architecture for larger-scale production use.

---

## Recommended next-step plan

## Phase 1 — close and commit the observability layer

### Goal
Make timeouted enrich runs analyzable and resumable enough for disciplined throughput experiments.

### Code tasks
1. **Commit current progress-persistence patch**
   - files:
     - `src/mygooglealertpapers/pipeline/enrich.py`
     - `src/mygooglealertpapers/db/repository.py`
     - `scripts/replay_validation.py`
     - `src/mygooglealertpapers/pipeline/enrich_stats.py`
     - `tests/test_enrich_cache_semantics.py`
2. ensure `batch_run.notes` always contains normalized dispatch stats during long runs
3. keep `processed_runnable_intents` persisted during execution, not only at finish

### Acceptance criteria
- full test suite passes
- a forced-timeout enrich run yields an interpretable report with partial-progress accounting
- report wording no longer conflates total planned savings with actually realized savings before timeout

---

## Phase 2 — promote a new live default lane experiment

### Goal
Stop treating Semantic Scholar as a first-line synchronous provider if the evidence keeps pointing the same way.

### Code / experiment tasks
1. **formalize the no-semanticscholar profile as an experimental promotion candidate**
2. run a second ablation on the `limit=120` slice against one of:
   - `no-crossref`
   - or `identifier-fastpath`
   - or `reduced biomedical title fallback`
3. compare:
   - processed completion fraction
   - projected full runtime
   - matched-source coverage
4. decide the next default live lane ordering

### Recommendation
I would prioritize:
1. `no-semanticscholar` baseline
2. `identifier-fastpath`
3. `no-crossref` or narrowed biomedical title fallback

Reason: it isolates whether the scalable core is already “identifier-first + OpenAlex batch + cheap providers”, before spending cycles tuning long-tail title search.

### Acceptance criteria
- at least one enrich-only ablation finishes comfortably inside the timeout budget
- the chosen default lane has a clear throughput advantage
- coverage loss is measured, not guessed

---

## Phase 3 — refactor enrich into explicit provider lanes

### Goal
Translate the Day 4 diagnosis into code structure rather than ad hoc profiles.

### Code tasks
1. split enrich execution into explicit lanes:
   - lane 1: identifier fastpath
   - lane 2: medium-cost title search
   - lane 3: slow fallback providers
2. add per-provider / per-lane budgets:
   - max requests
   - max wall-clock
   - optional provider disable-on-budget-exhaustion
3. allow later lanes to be skipped or deferred if earlier lanes already provide sufficient match evidence
4. preserve replay comparability for merge/dedup correctness

### Acceptance criteria
- enrich run emits per-lane accounting
- lane ordering is explicit in code and stats
- slow fallback providers can be disabled or deferred without rewriting policy profiles each time

---

## Phase 4 — decide whether concurrency is worth implementing now

### Recommendation
Do **not** jump straight to concurrency first.

Reason:
- current evidence says provider ordering and lane demotion are already high-yield
- concurrency without lane control may simply amplify rate-limit pain and make semantics harder to attribute

### Concurrency should come after
- semanticscholar demotion decision
- Crossref / biomedical fallback bottleneck isolation
- explicit lane accounting exists

If concurrency is still needed afterward:
- add provider-specific concurrency caps
- add rate-budgeters and circuit breakers
- keep deterministic replay for semantic checks and live profiling for throughput checks

---

## Phase 5 — parallel acquisition workstream only if needed

### If the immediate goal includes more 163 mail acquisition
Then run a smaller parallel sprint:
1. keep A+B as the current production path
2. add a page-prewarm probe for `read_mid` exposure
3. implement hybrid direct-fetch for mapped rows only
4. benchmark hybrid vs A+B on deep pages

### Otherwise
Do not let 163 optimization delay the central enrich-throughput work.

---

## Concrete priority-ordered task list

## P0 — should do next
1. commit the current timeout-safe progress/reporting patch
2. fold Day 4 throughput findings into the active docs layer
3. run the next provider-ablation experiment with `no-semanticscholar` as comparison baseline

## P1 — likely next engineering step
4. implement explicit enrich provider lanes / fastpath ordering
5. demote Semantic Scholar from synchronous default lane if repeated evidence holds
6. evaluate Crossref / biomedical title fallback as the next latency target

## P2 — after lane structure is stable
7. add resumable / budgeted long-run semantics
8. only then evaluate provider-specific concurrency

## P3 — parallel but secondary
9. continue 163 body-fetch optimization toward `read_mid` hybrid fetch

---

## Recommended immediate code tasks (smallest useful batch)

1. **Commit current working-tree runtime instrumentation**
2. **Add one more ablation profile**
   - likely `identifier_fastpath` or `no_crossref`
3. **Add a thin experiment runner wrapper** for Day 4 ablation matrix
   - input: source DB, limit, profile list, timeout
   - output: JSON + Markdown comparison bundle
4. **Update active docs**
   - `docs/13-project-phase-map-and-current-status-2026-04-22.md`
   - `docs/README.md`
   so they reflect:
   - Day 4 throughput diagnosis
   - new observability patch
   - current next-step recommendation

---

## Final recommendation

If we optimize for the highest-value next move, I would do this exact order:

1. **commit the current observability/partial-progress patch**
2. **treat Semantic Scholar demotion as the next default-live-lane decision candidate**
3. **run one more ablation to identify the post-Semantic-Scholar bottleneck**
4. **refactor enrich around explicit lanes before touching concurrency**

That path is the cleanest way to turn the project from “correct but timeout-prone” into “correct and operationally scalable.”
