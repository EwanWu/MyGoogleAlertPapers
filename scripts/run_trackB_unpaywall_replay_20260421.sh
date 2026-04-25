#!/usr/bin/env bash
# Track B: Unpaywall OA-enhancement experiment
# Replay with conditional_sources_v2 vs conditional_sources_v2_unpaywall
# Fixed seed: mgap_pkgB_large_slice150_seed_20260416_slice150.db
# 2026-04-21
#
# Usage:
#   UNPAYWALL_EMAIL=wuyue171@mails.ucas.ac.cn bash scripts/run_trackB_unpaywall_replay_20260421.sh
#
# Requirements:
#   - UNPAYWALL_EMAIL must be set (Unpaywall API requires institutional email)
#   - The v2 baseline DB from this seed already exists from Track A:
#       data/mgap_trackA_author_blob_fb_v2_20260421c.db
#     We will reuse its source_records for the merge-only comparison.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

UNPAYWALL_EMAIL="${UNPAYWALL_EMAIL:-}"
if [[ -z "$UNPAYWALL_EMAIL" ]]; then
    echo "ERROR: UNPAYWALL_EMAIL environment variable must be set."
    echo "Usage: UNPAYWALL_EMAIL=your@email.com bash scripts/run_trackB_unpaywall_replay_20260421.sh"
    exit 1
fi

export UNPAYWALL_EMAIL
export PYTHONPATH="$PROJECT_ROOT/src"

RUN_TAG="20260421b"
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"

# Use the v2 baseline DB source_records as the stable reference for merge-only comparison.
# This eliminates provider-response variability between separate enrich runs.
V2_DB="data/mgap_trackA_author_blob_fb_v2_20260421c.db"

# control: reuse v2 source_records via --reuse-source-records-from, then run merge+dedup only
CONTROL_DB="data/mgap_trackB_control_${RUN_TAG}.db"
CONTROL_REPORT="docs/validation/trackB-control-replay-${RUN_TAG}.json"

# treatment: copy source_records from existing v2 baseline, add Unpaywall, run merge+dedup
TREAT_DB="data/mgap_trackB_treat_${RUN_TAG}.db"
TREAT_REPORT="docs/validation/trackB-unpaywall-replay-${RUN_TAG}.json"

SUMMARY_JSON="docs/validation/trackB-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/trackB-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/trackB_unpaywall_${RUN_TAG}.log"

echo "v2_source_db=$V2_DB (source_records reused via --reuse-source-records-from)" | tee -a "$RUN_LOG"

# Step 1: control — run merge+dedup only (source_records from v2 baseline via --reuse)
echo "" | tee -a "$RUN_LOG"
echo "=== [control: v2 merge+dedup only, source_records from v2 baseline] ===" | tee -a "$RUN_LOG"
rm -f "$CONTROL_DB"
# --reuse-source-records-from copies v2 source_records into the fresh SEED_DB copy,
# then runs merge+dedup only. This avoids the shutil.copy2 overwrite bug.
python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$CONTROL_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$CONTROL_REPORT" \
  --reuse-source-records-from "$V2_DB" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages merge dedup \
  2>&1 | tee -a "$RUN_LOG" || true

# Step 2: treatment — fresh enrich+merge+dedup with Unpaywall enabled.
# Note: this re-runs enrich against live providers, so provider variability is expected.
# Key comparison: unpaywall source_records added, OA URL coverage, canonical/review delta
echo "" | tee -a "$RUN_LOG"
echo "=== [treatment: v2+unpaywall enrich+merge+dedup] ===" | tee -a "$RUN_LOG"
rm -f "$TREAT_DB"
UNPAYWALL_EMAIL="$UNPAYWALL_EMAIL" python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$TREAT_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_unpaywall.yaml \
  --report-out "$TREAT_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup \
  2>&1 | tee -a "$RUN_LOG" || true

# Generate summary
python3 - <<'PY' | tee -a "$RUN_LOG"
import json
from pathlib import Path

project = Path('.').resolve()
ctrl = json.loads((project / 'docs/validation/trackB-control-replay-20260421b.json').read_text())
treat = json.loads((project / 'docs/validation/trackB-unpaywall-replay-20260421b.json').read_text())

delta = {
    'matched_source_record_count': treat['matched_source_record_count'] - ctrl['matched_source_record_count'],
    'merged_metadata_proposal_count': treat['merged_metadata_proposal_count'] - ctrl['merged_metadata_proposal_count'],
    'canonical_paper_count': treat['canonical_paper_count'] - ctrl['canonical_paper_count'],
    'merge_review_queue_count': treat['merge_review_queue_count'] - ctrl['merge_review_queue_count'],
}

summary = {
    'run_tag': '20260421b',
    'control': 'conditional_sources_v2',
    'treatment': 'conditional_sources_v2_unpaywall',
    'control': ctrl,
    'treatment': treat,
    'delta': delta,
    'oa_url_coverage_note': (
        'OA URL coverage can be measured by querying source_record.url '
        'where source_name=unpaywall and url IS NOT NULL '
        'from the treatment DB.'
    ),
}

with (project / 'docs/validation/trackB-summary-20260421b.json').open('w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

md = f"""# Track B Unpaywall replay summary

## Run tag
{summary['run_tag']}

## Profiles
- control: `{summary['control']}`
- treatment: `{summary['treatment']}`

## Key metrics

| Metric | control (v2) | unpaywall | delta |
|---|---|---|---|
| matched_source_record_count | {ctrl['matched_source_record_count']} | {treat['matched_source_record_count']} | {delta['matched_source_record_count']} |
| merged_metadata_proposal_count | {ctrl['merged_metadata_proposal_count']} | {treat['merged_metadata_proposal_count']} | {delta['merged_metadata_proposal_count']} |
| canonical_paper_count | {ctrl['canonical_paper_count']} | {treat['canonical_paper_count']} | {delta['canonical_paper_count']} |
| merge_review_queue_count | {ctrl['merge_review_queue_count']} | {treat['merge_review_queue_count']} | {delta['merge_review_queue_count']} |
| severe_doi_conflict_count | {ctrl.get('severe_doi_conflict_count','N/A')} | {treat.get('severe_doi_conflict_count','N/A')} | N/A |

## OA URL coverage

To measure OA URL coverage from the treatment run:

```sql
SELECT COUNT(*) FROM source_record
WHERE source_name='unpaywall' AND url IS NOT NULL;
```

## Interpretation

- canonical_paper_count: primary correctness metric — should be flat or improved
- matched_source_record_count: Unpaywall adds records only for DOI-matched candidates
- merge_review_queue_count: should not increase if Unpaywall is not creating conflicts
"""

with (project / 'docs/validation/trackB-summary-20260421b.md').open('w') as f:
    f.write(md)

print(json.dumps({'status': 'done', 'summary': str(project / 'docs/validation/trackB-summary-20260421b.json')}, indent=2))
PY

echo "[$(date '+%F %T')] Track B replay complete" | tee -a "$RUN_LOG"
echo "summary_md=$SUMMARY_MD"