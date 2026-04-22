#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_TAG="20260421c"
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
V2_DB="data/mgap_trackA_author_blob_fb_v2_${RUN_TAG}.db"
TREAT_DB="data/mgap_trackA_author_blob_fb_treat_${RUN_TAG}.db"
V2_REPORT="docs/validation/trackA-author-blob-fb-v2-replay-${RUN_TAG}.json"
TREAT_REPORT="docs/validation/trackA-author-blob-fb-replay-${RUN_TAG}.json"
SUMMARY_JSON="docs/validation/trackA-author-blob-fb-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/trackA-author-blob-fb-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/trackA_author_blob_fb_${RUN_TAG}.log"

rm -f "$V2_DB" "$TREAT_DB" "$V2_REPORT" "$TREAT_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

echo "[$(date '+%F %T')] start Track A author_blob_fallback_only replay" | tee -a "$RUN_LOG"
echo "seed=$SEED_DB" | tee -a "$RUN_LOG"
echo "v2_db=$V2_DB" | tee -a "$RUN_LOG"
echo "treat_db=$TREAT_DB" | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$V2_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$V2_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$TREAT_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml \
  --report-out "$TREAT_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 - <<'PY' | tee -a "$RUN_LOG"
import json
from pathlib import Path

project = Path('.').resolve()
v2_report = project / 'docs/validation/trackA-author-blob-fb-v2-replay-20260421c.json'
treat_report = project / 'docs/validation/trackA-author-blob-fb-replay-20260421c.json'
summary_json = project / 'docs/validation/trackA-author-blob-fb-summary-20260421c.json'
summary_md = project / 'docs/validation/trackA-author-blob-fb-summary-20260421c.md'

v2 = json.loads(v2_report.read_text(encoding='utf-8'))
treat = json.loads(treat_report.read_text(encoding='utf-8'))

delta = {
    'matched_source_record_count': treat['matched_source_record_count'] - v2['matched_source_record_count'],
    'merged_metadata_proposal_count': treat['merged_metadata_proposal_count'] - v2['merged_metadata_proposal_count'],
    'normalized_only_fallback_proposal_count': treat['normalized_only_fallback_proposal_count'] - v2['normalized_only_fallback_proposal_count'],
    'canonical_paper_count': treat['canonical_paper_count'] - v2['canonical_paper_count'],
    'merge_review_queue_count': treat['merge_review_queue_count'] - v2['merge_review_queue_count'],
}

summary = {
    'run_tag': '20260421c',
    'control_profile': 'conditional_sources_v2',
    'treatment_profile': 'conditional_sources_v2_author_blob_fallback_only',
    'v2': v2,
    'treatment': treat,
    'delta': delta,
}

with summary_json.open('w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

md = f"""# Track A author_blob_fallback_only replay summary

## Run tag
{summary['run_tag']}

## Profiles
- control: `{summary['control_profile']}`
- treatment: `{summary['treatment_profile']}`

## Key metrics

| Metric | v2 (control) | author_blob_fb (treatment) | delta |
|---|---|---|---|
| matched_source_record_count | {v2['matched_source_record_count']} | {treat['matched_source_record_count']} | {delta['matched_source_record_count']} |
| merged_metadata_proposal_count | {v2['merged_metadata_proposal_count']} | {treat['merged_metadata_proposal_count']} | {delta['merged_metadata_proposal_count']} |
| normalized_only_fallback_proposal_count | {v2['normalized_only_fallback_proposal_count']} | {treat['normalized_only_fallback_proposal_count']} | {delta['normalized_only_fallback_proposal_count']} |
| canonical_paper_count | {v2['canonical_paper_count']} | {treat['canonical_paper_count']} | {delta['canonical_paper_count']} |
| merge_review_queue_count | {v2['merge_review_queue_count']} | {treat['merge_review_queue_count']} | {delta['merge_review_queue_count']} |
| severe_doi_conflict_count | {v2.get('severe_doi_conflict_count', 'N/A')} | {treat.get('severe_doi_conflict_count', 'N/A')} | N/A |

## Interpretation guide

- canonical_paper_count: primary correctness metric — negative delta means treatment lost canonical papers
- matched_source_record_count: provider match stability — large swings mean the patch is perturbing early matching
- normalized_only_fallback_proposal_count: fallback usage change
- merge_review_queue_count: human review burden — should stay flat or decrease

## Full raw results

### v2 (control)
```json
{json.dumps(v2, indent=2)}
```

### Treatment
```json
{json.dumps(treat, indent=2)}
```
"""

with summary_md.open('w', encoding='utf-8') as f:
    f.write(md)

print(json.dumps({'status': 'done', 'summary': str(summary_json)}, indent=2))
PY

echo "[$(date '+%F %T')] replay complete" | tee -a "$RUN_LOG"
echo "summary_json=$SUMMARY_JSON" | tee -a "$RUN_LOG"
echo "summary_md=$SUMMARY_MD" | tee -a "$RUN_LOG"