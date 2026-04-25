#!/usr/bin/env bash
# Track B Re-run (20260422): Unpaywall with fixed url field bug
# Isolated design: --stages merge dedup only for both arms (no live enrich variability)
# 
# Design:
#   Control: v2 source_records + merge+dedup only
#   Treatment: v2 source_records + Unpaywall enrich + merge+dedup
#
# Usage:
#   https_proxy=http://172.18.240.1:62049 \
#   http_proxy=http://172.18.240.1:62049 \
#   all_proxy=socks5://172.18.240.1:62049 \
#   UNPAYWALL_EMAIL=ewan.wu7@gmail.com \
#   bash scripts/run_trackB_unpaywall_rerun_20260422.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

UNPAYWALL_EMAIL="${UNPAYWALL_EMAIL:-}"
if [[ -z "$UNPAYWALL_EMAIL" ]]; then
    echo "ERROR: UNPAYWALL_EMAIL environment variable must be set."
    exit 1
fi

export UNPAYWALL_EMAIL
export PYTHONPATH="$PROJECT_ROOT/src"
export https_proxy="${https_proxy:-http://172.18.240.1:62049}"
export http_proxy="${http_proxy:-http://172.18.240.1:62049}"
export all_proxy="${all_proxy:-socks5://172.18.240.1:62049}"

RUN_TAG="20260422"
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
V2_DB="data/mgap_trackA_author_blob_fb_v2_20260421c.db"

CONTROL_DB="data/mgap_trackB_control_${RUN_TAG}.db"
CONTROL_REPORT="docs/validation/trackB-control-replay-${RUN_TAG}.json"

TREAT_DB="data/mgap_trackB_treat_${RUN_TAG}.db"
TREAT_REPORT="docs/validation/trackB-unpaywall-replay-${RUN_TAG}.json"

SUMMARY_JSON="docs/validation/trackB-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/trackB-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/trackB_unpaywall_${RUN_TAG}.log"

echo "[$(date '+%F %T')] === Track B re-run (20260422) ===" > "$RUN_LOG"
echo "email=$UNPAYWALL_EMAIL, proxy=$http_proxy" >> "$RUN_LOG"
echo "Control: v2 source_records + merge+dedup only" >> "$RUN_LOG"
echo "Treatment: v2 source_records + Unpaywall enrich + merge+dedup" >> "$RUN_LOG"

# Control: reuse v2 source_records, run merge+dedup only
echo "" | tee -a "$RUN_LOG"
echo "=== [control: v2 merge+dedup] ===" | tee -a "$RUN_LOG"
rm -f "$CONTROL_DB"
python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$CONTROL_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$CONTROL_REPORT" \
  --reuse-source-records-from "$V2_DB" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages merge dedup \
  2>&1 | tee -a "$RUN_LOG" || true

# Treatment: reuse v2 source_records + Unpaywall enrich + merge+dedup
# Note: Unpaywall-only enrich is much faster than full enrich
echo "" | tee -a "$RUN_LOG"
echo "=== [treatment: v2+unpaywall merge+dedup] ===" | tee -a "$RUN_LOG"
rm -f "$TREAT_DB"
UNPAYWALL_EMAIL="$UNPAYWALL_EMAIL" python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$TREAT_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_unpaywall.yaml \
  --report-out "$TREAT_REPORT" \
  --reuse-source-records-from "$V2_DB" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup \
  2>&1 | tee -a "$RUN_LOG" || true

# Generate summary
python3 - <<'PY' | tee -a "$RUN_LOG"
import json, sqlite3
from pathlib import Path

project = Path('.').resolve()
ctrl = json.loads((project / 'docs/validation/trackB-control-replay-20260422.json').read_text())
treat = json.loads((project / 'docs/validation/trackB-unpaywall-replay-20260422.json').read_text())

delta = {
    'canonical_paper_count': treat['canonical_paper_count'] - ctrl['canonical_paper_count'],
    'merge_review_queue_count': treat['merge_review_queue_count'] - ctrl['merge_review_queue_count'],
    'normalized_only_fallback_proposal_count': treat['normalized_only_fallback_proposal_count'] - ctrl['normalized_only_fallback_proposal_count'],
    'matched_source_record_count': treat['matched_source_record_count'] - ctrl['matched_source_record_count'],
}

# OA URL coverage from treatment DB
treat_db = f"data/mgap_trackB_treat_20260422.db"
oa_url_count = 0
up_total = 0
up_matched = 0
try:
    with sqlite3.connect(treat_db) as conn:
        up_total = conn.execute("SELECT COUNT(*) FROM source_record WHERE source_name='unpaywall'").fetchone()[0]
        up_matched = conn.execute("SELECT COUNT(*) FROM source_record WHERE source_name='unpaywall' AND matched=1").fetchone()[0]
        oa_url_count = conn.execute("SELECT COUNT(*) FROM source_record WHERE source_name='unpaywall' AND url IS NOT NULL AND url != ''").fetchone()[0]
except Exception as e:
    pass

summary = {
    'run_tag': '20260422',
    'control_profile': 'conditional_sources_v2',
    'treatment_profile': 'conditional_sources_v2_unpaywall',
    'control': ctrl,
    'treatment': treat,
    'delta': delta,
    'unpaywall_oa_url_count': oa_url_count,
    'unpaywall_total': up_total,
    'unpaywall_matched': up_matched,
    'oa_url_fill_rate': round(oa_url_count / up_matched, 3) if up_matched > 0 else None,
}

with (project / 'docs/validation/trackB-summary-20260422.json').open('w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

md = f"""# Track B Unpaywall re-run summary (20260422)

## Design
- Control: v2 source_records + merge+dedup only (no new enrich)
- Treatment: v2 source_records + Unpaywall enrich + merge+dedup
- Fix applied: best_oa_url now reads from best_oa_location.url (not top-level)

## Profiles
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_unpaywall`

## Key metrics

| Metric | Control (v2) | Treatment (+Unpaywall) | Delta |
|---|---|---|---|
| canonical_paper_count | {ctrl['canonical_paper_count']} | {treat['canonical_paper_count']} | **{delta['canonical_paper_count']}** |
| merge_review_queue_count | {ctrl['merge_review_queue_count']} | {treat['merge_review_queue_count']} | **{delta['merge_review_queue_count']}** |
| normalized_only_fallback | {ctrl['normalized_only_fallback_proposal_count']} | {treat['normalized_only_fallback_proposal_count']} | {delta['normalized_only_fallback_proposal_count']} |
| matched_source_record | {ctrl['matched_source_record_count']} | {treat['matched_source_record_count']} | {delta['matched_source_record_count']} |

## Unpaywall OA URL coverage

- Unpaywall total records: {up_total}
- Unpaywall matched: {up_matched}
- OA URL filled (url IS NOT NULL): **{oa_url_count}**
- Fill rate: {summary['oa_url_fill_rate']}

## Interpretation

- canonical_paper_count: primary correctness metric — should be flat
- merge_review_queue_count: should not increase
- OA URL fill rate: primary value metric — should be > 0 after bug fix

## Bug fix verification

If oa_url_count > 0, the url field bug is confirmed fixed.
If oa_url_count == 0 with up_matched > 0, the fix is not working.
"""

with (project / 'docs/validation/trackB-summary-20260422.md').open('w') as f:
    f.write(md)

print(f"Done. oa_url_count={oa_url_count}, canonical_delta={delta['canonical_paper_count']}")
PY

echo "[$(date '+%F %T')] Track B re-run complete" | tee -a "$RUN_LOG"