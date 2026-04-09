# Package 3 Plan: Enrichment Correctness and Conservative Merge Protection

## Purpose
After Package 1 (provider-level resumability) and Package 2 (authoritative cache hardening), the next major bottleneck is no longer basic execution control. It is correctness.

Package 3 should reduce false metadata attachment and protect the conservative canonical paper store from overly permissive enrichment and merge behavior.

---

## 1. Main correctness problems now in focus

### 1.1 Title-based fallback is still too permissive
Current title search can still attach the wrong provider record, especially when:
- title similarity is only moderate
- venue is weakly informative
- year is missing or noisy
- provider top hit is semantically related but not the same work

### 1.2 Merge conflict severity is not yet graded well enough
Current merge behavior still treats many conflicts too similarly.
Examples that need different handling:
- punctuation/capitalization differences
- venue formatting variants
- DOI disagreement
- PMID disagreement
- different conceptual works with similar titles

### 1.3 Conservative canonicalization still needs stronger protection
The project goal is a conservative main store. This means severe metadata disagreement should not be allowed to flow into a high-confidence canonical paper record just because a provider returned a plausible result.

---

## 2. Package-3 goals

1. Tighten title-based provider acceptance.
2. Make merge conflict handling more semantically aware.
3. Prevent severe-conflict proposals from being treated as high-confidence canonical truth.
4. Preserve useful provenance and diagnosability.

### Non-goals
- no new provider expansion yet
- no broad review UI/workflow yet
- no full version-linking redesign yet

---

## 3. Package-3 workstreams

## 3.1 Workstream A: title-fallback acceptance tightening

### Planned changes
- strengthen combined acceptance logic using:
  - title similarity
  - year compatibility
  - first-author family compatibility
  - venue compatibility
- downgrade or reject title-only matches with weak support
- treat DOI disagreement against extracted candidate DOI as a strong rejection signal
- use provider-specific caution, especially for PubMed title fallback

### Expected effect
- fewer wrong DOI/PMID attachments
- fewer false provider matches flowing into merge

---

## 3.2 Workstream B: merge conflict grading

### Planned conflict classes
#### Grade A: benign formatting conflict
- punctuation
- capitalization
- Unicode dash variants
- minor venue formatting differences

#### Grade B: moderate metadata divergence
- title truncation versus full title
- plausible version-like year difference
- venue family mismatch without identifier contradiction

#### Grade C: severe conflict
- DOI disagreement
- PMID disagreement
- semantically different titles despite partial similarity
- provider outputs clearly referring to different works

### Expected effect
- merge confidence becomes more meaningful
- later canonicalization can react differently to low-risk and high-risk conflicts

---

## 3.3 Workstream C: conservative canonical protection

### Planned policy
If a merged proposal contains severe conflict signals, it should not be promoted into a confident canonical paper representation without additional caution.

Possible implementation directions:
- lower merge confidence sharply
- mark proposal as provisional
- prevent use of severe-conflict identifiers as canonical truth

### Expected effect
- fewer clearly wrong canonical DOI / PMID assignments
- main store remains conservative by design

---

## 4. Validation approach

Use existing validation style:
- fresh small `issac` slices for quick iteration
- compare against known bad examples from earlier 30/100-email validation

### Metrics to watch
- number of severe DOI conflicts
- number of severe PMID conflicts
- overall merged-proposal conflict rate
- number of canonical records with obviously wrong identifiers in sampled inspection
- provider match counts before/after tightening

### Success criteria
1. fewer severe false matches make it into merged proposals
2. canonical layer receives fewer obviously wrong identifiers
3. overall system remains conservative even if recall drops modestly

---

## 5. Recommended immediate coding order

1. tighten acceptance logic in enrichment base/provider matching helpers
2. add conflict grading logic in merge stage
3. add conservative guardrails before canonical promotion
4. re-run a controlled small validation slice and compare examples

---

## 6. Decision summary
Package 3 is the next correctness-focused phase.

Package 1 and Package 2 improved execution control and cache behavior.
Package 3 should now improve metadata trustworthiness and protect the canonical paper store from false certainty.
